"""Publish complete release assets, safely retrying observed GitHub 5xx errors."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def gh(*args):
    for attempt in range(5):
        result = subprocess.run(['gh', *args], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        if not any(status in result.stderr for status in ('500', '502', '503', '504')):
            raise RuntimeError(result.stderr)
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(result.stderr)


def main():
    tag = os.environ['TAG']
    for attempt in range(5):
        view = subprocess.run(['gh', 'release', 'view', tag, '--json', 'isDraft'], capture_output=True, text=True)
        if view.returncode == 0:
            if not json.loads(view.stdout)['isDraft']:
                print('Release already published; preserving its existing immutable assets.')
                return
            break
        if not ('404' in view.stderr or 'release not found' in view.stderr.lower()):
            time.sleep(3 * (attempt + 1))
            continue
        try:
            gh('release', 'create', tag, '--draft', '--verify-tag', '--title', 'TicTacTest ' + tag,
               '--notes-file', 'release-notes.md')
            break
        except RuntimeError:
            # A create request can succeed server-side and still return 5xx.
            time.sleep(3)
    else:
        raise RuntimeError('Could not prepare a draft release')
    files = sorted(Path('release-assets').iterdir())
    if len(files) != 8:
        raise RuntimeError('Expected JAR, frontend, tools, manifest and four checksums')
    for file in files:
        gh('release', 'upload', tag, str(file), '--clobber')
    with tempfile.TemporaryDirectory() as directory:
        gh('release', 'download', tag, '--dir', directory)
        subprocess.run('sha256sum -c *.sha256', shell=True, cwd=directory, check=True)
    gh('release', 'edit', tag, '--draft=false')
    print('Complete verified release published: ' + tag)


if __name__ == '__main__':
    main()
