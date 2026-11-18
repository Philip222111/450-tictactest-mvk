"""Real filesystem regression tests; no AWS, package manager or systemd actions."""
import base64
from contextlib import nullcontext
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('atomic_runtime', ROOT / 'infrastructure/runtime/atomic_runtime.py')
atomic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atomic)


class AtomicRuntimeTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def entry(self, path, data, mode=0o644):
        return {'path': str(path), 'data': base64.b64encode(data).decode(),
                'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode}

    def test_bootstrap_compressed_bundle_cli(self):
        target = self.root / 'installer.py'
        entries = [self.entry(target, b'valid = True\n')]
        payload = base64.b64encode(gzip.compress(json.dumps(entries).encode())).decode()
        with patch.object(sys, 'argv', ['-', 'bundle', payload]), patch.object(atomic, 'deployment_lock', return_value=nullcontext()) as lock:
            atomic.main()
            lock.assert_called_once()
        self.assertEqual(target.read_bytes(), b'valid = True\n')

    def test_file_cli_locks_before_publication(self):
        target = self.root / 'nginx.conf'
        source = self.root / 'candidate'
        source.write_bytes(b'complete config')
        with patch.object(sys, 'argv', ['atomic_runtime.py', 'file', str(target), str(source), '644']), patch.object(atomic, 'deployment_lock', return_value=nullcontext()) as lock:
            atomic.main()
            lock.assert_called_once()
        self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_interpreter_sees_old_complete_script_while_new_file_is_half_written(self):
        target = self.root / 'deploy_release.py'
        old = b"print('old-complete')\n"
        new = b"print('new-complete')\n" + b'# new runtime\n' * 1000
        target.write_bytes(old)
        half_written = threading.Event()
        finish = threading.Event()
        errors = []
        real_fdopen = os.fdopen

        class PausedWriter:
            def __init__(self, file): self.file = file
            def __enter__(self): return self
            def __exit__(self, *args): return self.file.__exit__(*args)
            def __getattr__(self, name): return getattr(self.file, name)
            def write(self, data):
                half = len(data) // 2
                self.file.write(data[:half])
                self.file.flush()
                half_written.set()
                if not finish.wait(5): raise RuntimeError('test writer timed out')
                self.file.write(data[half:])

        def writer():
            try: atomic.replace_file(target, new)
            except BaseException as error: errors.append(error)

        with patch.object(atomic.os, 'fdopen', side_effect=lambda *a, **kw: PausedWriter(real_fdopen(*a, **kw))):
            worker = threading.Thread(target=writer)
            worker.start()
            try:
                self.assertTrue(half_written.wait(5))
                self.assertEqual(target.read_bytes(), old)
                result = subprocess.run([sys.executable, '-B', str(target)], check=True,
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.stdout.strip(), 'old-complete')
            finally:
                finish.set()
                worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        result = subprocess.run([sys.executable, '-B', str(target)], check=True,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.stdout.strip(), 'new-complete')
        self.assertEqual(target.read_bytes(), new)
        self.assertEqual(list(self.root.iterdir()), [target])

    @unittest.skipUnless(os.name == 'posix', 'open-inode semantics require Linux/POSIX')
    def test_reader_open_before_replace_retains_old_inode(self):
        target = self.root / 'installer.py'
        target.write_bytes(b'old-first\nold-last\n')
        with target.open('rb', buffering=0) as reader:
            self.assertEqual(reader.read(10), b'old-first\n')
            atomic.replace_file(target, b'new-complete\n')
            self.assertEqual(reader.read(), b'old-last\n')
        self.assertEqual(target.read_bytes(), b'new-complete\n')

    def test_replace_failure_and_failed_staging_leave_destination_unchanged(self):
        target = self.root / 'installer.py'
        target.write_bytes(b'healthy')
        for operation in ('replace', 'fsync'):
            with self.subTest(operation=operation), patch.object(atomic.os, operation, side_effect=OSError('disk failure')):
                with self.assertRaises(OSError): atomic.replace_file(target, b'new')
            self.assertEqual(target.read_bytes(), b'healthy')
            self.assertEqual(list(self.root.iterdir()), [target])

    def test_all_bundle_validation_finishes_before_first_publication(self):
        first = self.root / 'first.py'
        second = self.root / 'second.py'
        first.write_bytes(b'old = 1\n')
        good = self.entry(first, b'new = 2\n')
        bad_syntax = self.entry(second, b'def broken(\n')
        bad_hash = {**self.entry(second, b'valid = 1\n'), 'sha256': '0' * 64}
        for bad in (bad_syntax, bad_hash):
            with self.subTest(bad=bad['sha256']), self.assertRaises((SyntaxError, ValueError)):
                atomic.install_bundle([good, bad])
            self.assertEqual(first.read_bytes(), b'old = 1\n')
            self.assertFalse(second.exists())
            self.assertEqual(list(self.root.iterdir()), [first])

    def test_shell_validation_failure_leaves_existing_runtime_untouched(self):
        first = self.root / 'installer.py'
        first.write_bytes(b'healthy = True\n')
        entries = [self.entry(first, b'updated = True\n'),
                   self.entry(self.root / 'provision.sh', b'if then broken\n', 0o755)]
        if os.name == 'posix':
            with self.assertRaises(subprocess.CalledProcessError): atomic.install_bundle(entries)
        else:
            with patch.object(atomic.subprocess, 'run', side_effect=subprocess.CalledProcessError(2, 'bash')):
                with self.assertRaises(subprocess.CalledProcessError): atomic.install_bundle(entries)
        self.assertEqual(first.read_bytes(), b'healthy = True\n')
        self.assertEqual(list(self.root.iterdir()), [first])

    def test_rollback_failure_is_reported_instead_of_success(self):
        first = self.root / 'first.py'
        first.write_bytes(b'old = True\n')
        last = self.root / 'last.py'
        entries = [self.entry(first, b'new = True\n'), self.entry(last, b'last = True\n')]
        real_replace = os.replace
        count = 0
        def replace(source, target):
            nonlocal count
            count += 1
            if count > 1: raise OSError('persistent storage failure')
            return real_replace(source, target)
        with patch.object(atomic.os, 'replace', side_effect=replace):
            with self.assertRaisesRegex(RuntimeError, 'rollback incomplete'): atomic.install_bundle(entries)
        self.assertEqual(first.read_bytes(), b'new = True\n')
        self.assertFalse(last.exists())
        self.assertEqual(list(self.root.iterdir()), [first])

    def test_bundle_publication_failure_restores_files_and_removes_new_targets(self):
        first = self.root / 'first.py'
        created = self.root / 'created.py'
        failed = self.root / 'last.py'
        first.write_bytes(b'old = 1\n')
        entries = [self.entry(first, b'new = 2\n'), self.entry(created, b'created = 3\n'),
                   self.entry(failed, b'last = 4\n')]
        real_replace = os.replace
        def replace(source, target):
            if Path(target) == failed: raise OSError('publication failed')
            return real_replace(source, target)
        with patch.object(atomic.os, 'replace', side_effect=replace):
            with self.assertRaisesRegex(OSError, 'publication failed'): atomic.install_bundle(entries)
        self.assertEqual(first.read_bytes(), b'old = 1\n')
        self.assertEqual(list(self.root.iterdir()), [first])

    def test_successful_runtime_update_preserves_application_versions_and_state(self):
        state = self.root / 'opt/tictactest'
        state.mkdir(parents=True)
        files = {'app.jar': b'original jar', 'backend-version.json': b'{"version":"1.3.3"}',
                 'deployment-state.json': b'{"tag":"v1.3.4"}',
                 'frontend/version.json': b'{"version":"1.3.4"}'}
        for name, data in files.items():
            path = state / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
        entries = []
        for source in ('atomic_runtime.py', 'deploy_release.py', 'provision.sh', 'nginx.conf', 'tictactest.service'):
            entries.append(self.entry(self.root / 'runtime' / source,
                                      (ROOT / 'infrastructure/runtime' / source).read_bytes(),
                                      0o755 if source.endswith('.sh') else 0o644))
        # Use real bash on Linux; simulate only its successful exit on Windows.
        real_run = subprocess.run
        with patch.object(atomic.subprocess, 'run', wraps=real_run if os.name == 'posix' else None) as syntax:
            atomic.install_bundle(entries)
            self.assertEqual(syntax.call_args.args[0][:2], ['bash', '-n'])
        for name, data in files.items(): self.assertEqual((state / name).read_bytes(), data)
        for entry in entries:
            path = Path(entry['path'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])
            if os.name == 'posix': self.assertEqual(path.stat().st_mode & 0o777, entry['mode'])

    def test_bootstrap_and_direct_provision_use_atomic_helper_and_same_lock(self):
        bootstrap = (ROOT / 'infrastructure/web.tf').read_text()
        provision = (ROOT / 'infrastructure/runtime/provision.sh').read_text()
        installer = (ROOT / 'infrastructure/runtime/deploy_release.py').read_text()
        for text in (bootstrap, provision, installer, Path(atomic.__file__).read_text()):
            self.assertIn('/var/lock/tictactest-deployment.lock', text)
        self.assertNotIn('| base64 -d >', bootstrap)
        self.assertIn('file("${path.module}/runtime/atomic_runtime.py")', bootstrap)
        self.assertLess(bootstrap.index('flock -x 9'), bootstrap.index('python3 - bundle'))
        self.assertLess(provision.index('flock -x 9'), provision.index('dnf install'))
        self.assertIn('/proc/self/fd/9 -ef', provision)
        for target in ('/usr/local/bin/ttyd', '/opt/tictactest/config.js', '/etc/nginx/nginx.conf'):
            self.assertIn('"$atomic" file ' + target, provision)
        self.assertLess(provision.index('nginx -t -c'), provision.index('"$atomic" file /etc/nginx/nginx.conf'))

    @unittest.skipUnless(os.name == 'posix', 'real flock requires Linux/POSIX')
    def test_provision_lock_excludes_deployment_process(self):
        path = self.root / 'deployment.lock'
        code = """import fcntl, sys
with open(sys.argv[1], 'a') as lock:
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: sys.exit(42)
"""
        with atomic.deployment_lock(path):
            result = subprocess.run([sys.executable, '-B', '-c', code, str(path)], timeout=5)
            self.assertEqual(result.returncode, 42)
        result = subprocess.run([sys.executable, '-B', '-c', code, str(path)], timeout=5)
        self.assertEqual(result.returncode, 0)

    @unittest.skipUnless(os.name == 'posix', 'inherited flock requires Linux/POSIX')
    def test_inherited_fd_is_reused_without_deadlock_or_unlocking_parent(self):
        code = """import fcntl, importlib.util, os, pathlib, sys
spec = importlib.util.spec_from_file_location('atomic', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
path = pathlib.Path(sys.argv[2])
with path.open('a') as parent:
    os.dup2(parent.fileno(), 9)
    fcntl.flock(9, fcntl.LOCK_EX)
    with module.deployment_lock(path): pass
    with path.open('a') as other:
        try: fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: pass
        else: raise RuntimeError('parent lock was unlocked')
    os.close(9)
"""
        subprocess.run([sys.executable, '-B', '-c', code, atomic.__file__,
                        str(self.root / 'deployment.lock')], check=True, timeout=5)


if __name__ == '__main__':
    unittest.main()
