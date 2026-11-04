"""Package immutable release assets; compare complete releases, never just commits."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from urllib.request import urlopen

BACKEND = ('src/main/', 'build.gradle', 'settings.gradle', 'gradle/', 'gradle.properties')
FRONTEND = ('frontend/',)
SHARED = ('scripts/release_assets.py', 'deploy/', 'infrastructure/runtime/')


def changes(paths):
    shared = any(p.startswith(SHARED) for p in paths)
    return {'backend': shared or any(p.startswith(BACKEND) for p in paths),
            'frontend': shared or any(p.startswith(FRONTEND) for p in paths)}


def package(tag, target=Path('release-assets')):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Expected semantic release tag')
    version = tag[1:]
    previous = subprocess.run(['git', 'describe', '--tags', '--abbrev=0', '--match', 'v[0-9]*', tag + '^'],
                              capture_output=True, text=True)
    previous = previous.stdout.strip() if previous.returncode == 0 else None
    paths = subprocess.check_output(['git', 'diff', '--name-only', previous, tag], text=True).splitlines() if previous else []
    changed = changes(paths) if previous else {'backend': True, 'frontend': True}
    target.mkdir(exist_ok=True)
    jar = target / f'tictactest-{version}.jar'
    jar.write_bytes(Path(f'build/libs/{jar.name}').read_bytes())
    frontend = target / f'tictactest-frontend-{version}.zip'
    with zipfile.ZipFile(frontend, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(Path('frontend').rglob('*')):
            if file.is_file() and file.name not in ('config.js', 'version.json'):
                archive.write(file, file.relative_to('frontend').as_posix())
        archive.writestr('version.json', json.dumps({'version': version}) + '\n')
    manifest = {'tag': tag, 'version': version, 'previous_tag': previous, 'changed': changed,
                'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (jar, frontend)}}
    (target / 'deployment.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for file in (jar, frontend, target / 'deployment.json'):
        file.with_name(file.name + '.sha256').write_text(hashlib.sha256(file.read_bytes()).hexdigest() + '  ' + file.name + '\n')
    # Local launcher is also shipped, so running the app needs no source checkout.
    tools = target / f'tictactest-tools-{version}.zip'
    digests = {'ttyd.x86_64': '8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55',
               'ttyd.win32.exe': 'e33a27501b10b96981335bcba938b1145c7f52551a343e72160f00ab71832b37'}
    with zipfile.ZipFile(tools, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write('scripts/local_run.py', 'local_run.py')
        for name, digest in digests.items():
            with urlopen('https://github.com/tsl0922/ttyd/releases/download/1.7.7/' + name, timeout=30) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError('ttyd publisher checksum mismatch')
            archive.writestr(name, data)
    tools.with_name(tools.name + '.sha256').write_text(hashlib.sha256(tools.read_bytes()).hexdigest() + '  ' + tools.name + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    package(sys.argv[1])
