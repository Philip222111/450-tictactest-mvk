"""Atomic runtime file publication. Embedded in bootstrap, so it can install itself."""
import argparse
import ast
import base64
from contextlib import contextmanager
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

LOCK_PATH = Path('/var/lock/tictactest-deployment.lock')


@contextmanager
def deployment_lock(path=LOCK_PATH):
    import fcntl
    # Bootstrap/provision.sh pass their locked open-file description as fd 9.
    # Reuse it instead of deadlocking against a lock held by our own parent.
    try:
        inherited = os.fstat(9)
        expected = path.stat()
        inherited_lock = (inherited.st_dev, inherited.st_ino) == (expected.st_dev, expected.st_ino)
    except OSError:
        inherited_lock = False
    if inherited_lock:
        fcntl.flock(9, fcntl.LOCK_EX)
        yield  # Do not unlock the parent's open-file description.
    else:
        with path.open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield


def stage_file(target, data, mode):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + target.name + '.', dir=target.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.chmod(staged, mode)
            os.fsync(output.fileno())
        return staged
    except BaseException:
        staged.unlink(missing_ok=True)
        raise


def replace_file(target, data, mode=0o644):
    """Existing readers retain the old inode; new opens see the complete new file."""
    staged = stage_file(target, data, mode)
    try:
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)


def install_bundle(entries):
    """Validate/stage everything first; restore published files on ordinary failures."""
    prepared = []
    published = []
    try:
        targets = set()
        for entry in entries:
            target = Path(entry['path'])
            if target in targets:
                raise ValueError('Duplicate runtime target')
            targets.add(target)
            data = base64.b64decode(entry['data'], validate=True)
            if hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('Runtime checksum mismatch: ' + str(target))
            mode = entry['mode']
            if mode not in (0o644, 0o755):
                raise ValueError('Unsupported runtime file mode')
            if target.is_symlink():
                raise ValueError('Runtime target must not be a symlink')
            previous = (target.read_bytes(), stat.S_IMODE(target.stat().st_mode)) if target.exists() else None
            staged = stage_file(target, data, mode)
            prepared.append((target, staged, previous))
            if target.suffix == '.py':
                ast.parse(data, filename=str(target))
            elif target.suffix == '.sh':
                subprocess.run(['bash', '-n', str(staged)], check=True)
        for target, staged, previous in prepared:
            os.replace(staged, target)
            published.append((target, previous))
    except BaseException:
        failures = []
        for target, previous in reversed(published):
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    replace_file(target, *previous)
            except OSError as error:
                failures.append(str(error))
        if failures:
            raise RuntimeError('Runtime rollback incomplete: ' + '; '.join(failures))
        raise
    finally:
        for _, staged, _ in prepared:
            staged.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    bundle = commands.add_parser('bundle')
    bundle.add_argument('payload')
    file = commands.add_parser('file')
    file.add_argument('target', type=Path)
    file.add_argument('source', type=Path)
    file.add_argument('mode', type=lambda value: int(value, 8), choices=(0o644, 0o755))
    args = parser.parse_args()
    with deployment_lock():
        if args.command == 'bundle':
            install_bundle(json.loads(gzip.decompress(base64.b64decode(args.payload, validate=True))))
        else:
            replace_file(args.target, args.source.read_bytes(), args.mode)


if __name__ == '__main__':
    main()
