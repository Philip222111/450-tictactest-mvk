"""Infrastructure-owned installer. Only consumes verified GitHub release assets."""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
import zipfile

ROOT = Path('/opt/tictactest')


def read_version(path):
    return json.loads(path.read_text())['version'] if path.exists() else None


def preflight(jar, version, identity=None):
    with zipfile.ZipFile(jar) as archive:
        manifest = archive.read('META-INF/MANIFEST.MF').decode()
    if not re.search(r'^Implementation-Version: ' + re.escape(version) + r'\s*$', manifest, re.M):
        raise RuntimeError('JAR manifest version differs from release')
    command = ['java', '-Xmx48m', '-jar', str(jar)]
    credentials = ({'user': identity[0], 'group': identity[1], 'extra_groups': []}
                   if identity else {})
    process = subprocess.Popen(command, stdin=subprocess.PIPE, start_new_session=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **credentials)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 20
            output = b''
            selected = False
            while time.monotonic() < deadline:
                for key, _ in selector.select(.2):
                    chunk = os.read(key.fd, 4096)
                    if not chunk:
                        raise RuntimeError('JAR exited before game prompt')
                    output += chunk
                    if b'Gegner (1=Greedy, 2=Perfect):' in output and not selected:
                        process.stdin.write(b'1\n')
                        process.stdin.flush()
                        selected = True
                    if b'(0-8)' in output and process.poll() is None:
                        return
                if process.poll() is not None:
                    break
        raise RuntimeError('JAR cannot start or has no game prompt within 20 seconds')
    finally:
        # Stop the isolated probe group, including any descendants.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdin.close()
        process.stdout.close()


def service_identity():
    values = []
    for property_name in ('User', 'Group'):
        value = subprocess.check_output(
            ['systemctl', 'show', 'tictactest', '--property=' + property_name, '--value'], text=True).strip()
        if not re.fullmatch(r'[a-z_][a-z0-9_-]*', value) or value == 'root':
            raise RuntimeError('Expected explicit unprivileged systemd User and Group')
        values.append(value)
    return tuple(values)


def atomic_bytes(path, data):
    staged = path.with_name(path.name + '.next')
    staged.write_bytes(data)
    os.chmod(staged, 0o644)
    os.replace(staged, path)


def activate_frontend(frontend, version):
    # A fresh directory on the same filesystem also protects re-deploys of the active version.
    target = Path(tempfile.mkdtemp(prefix='frontend-' + version + '-', dir=ROOT / 'releases'))
    link = ROOT / 'frontend.next'
    try:
        shutil.copytree(frontend, target, dirs_exist_ok=True)
        os.chmod(target, 0o755)
        for path in target.rglob('*'):
            os.chmod(path, 0o755 if path.is_dir() else 0o644)
        link.unlink(missing_ok=True)
        link.symlink_to(target, target_is_directory=True)
        os.replace(link, ROOT / 'frontend')
    except Exception:
        link.unlink(missing_ok=True)
        shutil.rmtree(target)
        raise


def deploy(source, tag, force=False):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Invalid tag')
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        for name in ('deployment.json', 'deployment.json.sha256'):
            subprocess.run(['aws', 's3', 'cp', source + name, str(temp / name), '--only-show-errors'], check=True)
        for check in temp.glob('*.sha256'):
            expected, filename = check.read_text().split()
            if Path(filename).name != filename or hashlib.sha256((temp / filename).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Checksum mismatch: ' + filename)
        manifest = json.loads((temp / 'deployment.json').read_text())
        if manifest['tag'] != tag or manifest['version'] != tag[1:]:
            raise RuntimeError('Release manifest has wrong tag/version')
        statefile = ROOT / 'deployment-state.json'
        state = json.loads(statefile.read_text()) if statefile.exists() else {}
        # Drift, a skipped release or a rollback means the target needs both components.
        force = force or state.get('tag') != manifest['previous_tag']
        changed = {part: force or manifest['changed'][part] for part in ('backend', 'frontend')}
        version = manifest['version']
        for part, name in [('backend', f'tictactest-{version}.jar'),
                           ('frontend', f'tictactest-frontend-{version}.zip')]:
            if changed[part]:
                subprocess.run(['aws', 's3', 'cp', source + name, str(temp / name), '--only-show-errors'], check=True)
                if hashlib.sha256((temp / name).read_bytes()).hexdigest() != manifest['files'][name]:
                    raise RuntimeError('Release artifact checksum mismatch')
        jar = temp / f'tictactest-{version}.jar'
        if changed['backend']:
            preflight(jar, version)  # A broken artifact never replaces the healthy application.
        frontend = temp / 'frontend'
        if changed['frontend']:
            frontend.mkdir()
            with zipfile.ZipFile(temp / f'tictactest-frontend-{version}.zip') as archive:
                for name in archive.namelist():
                    if name.startswith('/') or '..' in Path(name).parts or name == 'config.js':
                        raise RuntimeError('Unsafe frontend archive or infrastructure config included')
                archive.extractall(frontend)
            if read_version(frontend / 'version.json') != version or not (frontend / 'index.html').is_file():
                raise RuntimeError('Frontend archive is incomplete or has wrong version')
        if changed['backend']:
            app = ROOT / 'app.jar'
            old = app.read_bytes() if app.exists() else None
            metadata = ROOT / 'backend-version.json'
            old_metadata = metadata.read_bytes() if metadata.exists() else None
            identity = service_identity()
            try:
                shutil.copyfile(jar, ROOT / 'app.jar.next')
                os.chmod(ROOT / 'app.jar.next', 0o644)
                os.replace(ROOT / 'app.jar.next', app)
                subprocess.run(['systemctl', 'restart', 'tictactest'], check=True)
                for attempt in range(20):
                    try:
                        with urlopen('http://127.0.0.1/terminal/token', timeout=2) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(.5)
                else:
                    raise RuntimeError('Terminal did not become healthy')
                preflight(app, version, identity=identity)
                atomic_bytes(metadata, (json.dumps({'version': version}) + '\n').encode())
            except Exception:
                if old is not None:
                    atomic_bytes(app, old)
                    if old_metadata is not None:
                        atomic_bytes(metadata, old_metadata)
                    else:
                        metadata.unlink(missing_ok=True)
                    subprocess.run(['systemctl', 'restart', 'tictactest'], check=True)
                    if old_metadata is not None:
                        preflight(app, json.loads(old_metadata)['version'], identity=identity)
                else:
                    subprocess.run(['systemctl', 'stop', 'tictactest'], check=True)
                    app.unlink(missing_ok=True)
                    metadata.unlink(missing_ok=True)
                raise
        if changed['frontend']:
            activate_frontend(frontend, version)
        actual = {'backend': read_version(ROOT / 'backend-version.json'),
                  'frontend': read_version(ROOT / 'frontend/version.json')}
        for part in changed:
            if changed[part] and actual[part] != version:
                raise RuntimeError('Installed version mismatch: ' + part)
        statefile.write_text(json.dumps({'tag': tag, **actual}) + '\n')
        print(json.dumps({'tag': tag, 'changed': changed, 'versions': actual}))


if __name__ == '__main__':
    import fcntl  # Linux-only locking; helpers remain importable by Windows unit tests.
    with open('/var/lock/tictactest-deployment.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        deploy(sys.argv[1], sys.argv[2], '--force' in sys.argv[3:])
