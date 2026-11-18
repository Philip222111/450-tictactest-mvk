"""Package immutable release assets; compare complete releases, never just commits."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from urllib.request import urlopen
from release_metadata import validate_tag

BACKEND = ('src/main/', 'build.gradle', 'settings.gradle', 'gradle/', 'gradle.properties', 'gradlew')
FRONTEND = ('frontend/',)
SHARED = ('scripts/release_assets.py', 'deploy/', 'infrastructure/runtime/')


def previous_release(tag):
    """Latest published ancestor (publication time, then tag); drafts/bare tags excluded."""
    validate_tag(tag)
    subprocess.run(['git', 'rev-parse', '--verify', tag + '^{commit}'],
                   capture_output=True, text=True, check=True)
    result = subprocess.run(
        ['gh', 'api', '--paginate', '--slurp', 'repos/{owner}/{repo}/releases?per_page=100'],
        capture_output=True, text=True, check=True, timeout=60)
    releases = [release for page in json.loads(result.stdout) for release in page]
    current = next((r for r in releases if r['tag_name'] == tag and not r['draft'] and r['published_at']), None)
    candidates = []
    for release in releases:
        candidate = release['tag_name']
        if candidate == tag or release['draft'] or not release['published_at']:
            continue
        try:
            validate_tag(candidate)
        except ValueError:
            continue
        if current and release['published_at'] > current['published_at']:
            continue
        # Missing fetched tags and other git errors are errors, not "first release".
        ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', candidate, tag],
                                  capture_output=True, text=True)
        if ancestor.returncode not in (0, 1):
            raise RuntimeError('Cannot resolve published release ancestry: ' + candidate)
        if ancestor.returncode == 0:
            candidates.append((release['published_at'], candidate))
    return max(candidates)[1] if candidates else None


def changes(paths):
    shared = any(p.startswith(SHARED) for p in paths)
    return {'backend': shared or any(p.startswith(BACKEND) for p in paths),
            'frontend': shared or any(p.startswith(FRONTEND) for p in paths)}


def package(tag, target=Path('release-assets')):
    validate_tag(tag)
    version = tag[1:]
    previous = previous_release(tag)
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
