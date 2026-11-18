"""CI and manual deployment: consumes release-assets, never builds or runs IaC."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.request import urlopen
from release_metadata import published_release

PARTS = {'backend': '/backend-version.json', 'frontend': '/version.json'}


def verified_manifest(tag, directory=Path('release-assets')):
    published_release(tag)
    data = (directory / 'deployment.json').read_bytes()
    digest, name = (directory / 'deployment.json.sha256').read_text().split()
    if name != 'deployment.json' or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Invalid release manifest checksum')
    manifest = json.loads(data)
    if manifest['tag'] != tag or manifest['version'] != tag[1:]:
        raise ValueError('Release manifest has wrong tag/version')
    for part in PARTS:
        if type(manifest['changed'][part]) is not bool:
            raise ValueError('Invalid component change flag')
    for name in (f'tictactest-{tag[1:]}.jar', f'tictactest-frontend-{tag[1:]}.zip'):
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != manifest['files'][name]:
            raise ValueError('Release artifact checksum mismatch: ' + name)
    return manifest


def public_version(path):
    with urlopen(os.environ['APP_URL'].rstrip('/') + path, timeout=4) as response:
        version = json.load(response)['version']
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Invalid public component version')
    return version


def expected_versions(tag, manifest, report, baseline, force):
    if report.get('tag') != tag:
        raise ValueError('Installer reported wrong release tag')
    flags = report['changed']
    for part in PARTS:
        if type(flags[part]) is not bool or ((force or manifest['changed'][part]) and not flags[part]):
            raise ValueError('Installer reported invalid change flags')
    # The installer may force BOTH components when its persisted predecessor differs.
    if flags != manifest['changed'] and flags != dict.fromkeys(PARTS, True):
        raise ValueError('Installer reported inconsistent recovery flags')
    expected = {part: tag[1:] if flags[part] else baseline[part] for part in PARTS}
    if any(report['versions'][part] != expected[part] for part in PARTS):
        raise ValueError('Installer versions differ from independently expected versions')
    return expected


def aws(*args):
    result = subprocess.run(['aws', *args, '--output', 'json'], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main():
    tag = os.environ['TAG']
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Invalid tag')
    manifest = verified_manifest(tag)
    force_all = os.environ.get('FORCE') == 'true'
    baseline = {}
    for part, path in PARTS.items():
        if not force_all and not manifest['changed'][part]:
            baseline[part] = public_version(path)
    source = f"s3://{os.environ['ARTIFACT_BUCKET']}/releases/{tag}/"
    subprocess.run(['aws', 's3', 'sync', 'release-assets/', source, '--only-show-errors'], check=True)
    force = ' --force' if os.environ.get('FORCE') == 'true' else ''
    command = f'python3 /usr/local/lib/tictactest/deploy_release.py {source} {tag}{force}'
    result = aws('ssm', 'send-command', '--instance-ids', os.environ['INSTANCE_ID'],
                 '--document-name', 'AWS-RunShellScript', '--timeout-seconds', '120',
                 '--parameters', json.dumps({'commands': [command], 'executionTimeout': ['180']}))
    command_id = result['Command']['CommandId']
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        try:
            result = aws('ssm', 'get-command-invocation', '--command-id', command_id,
                         '--instance-id', os.environ['INSTANCE_ID'])
        except RuntimeError as error:
            if 'InvocationDoesNotExist' not in str(error): raise
            time.sleep(3)
            continue
        if result['Status'] in ('Pending', 'InProgress', 'Delayed'):
            time.sleep(3)
            continue
        print(result.get('StandardOutputContent', ''))
        if result['Status'] != 'Success':
            raise RuntimeError(result.get('StandardErrorContent', '') + ' SSM status: ' + result['Status'])
        report = json.loads(result['StandardOutputContent'].strip().splitlines()[-1])
        break
    else:
        raise RuntimeError('Deployment timed out after 240 seconds')
    versions = expected_versions(tag, manifest, report, baseline, force_all)
    for part, path in PARTS.items():
        expected = versions[part]
        for attempt in range(20):
            try:
                actual = public_version(path)
                if actual == expected:
                    print(f'{part}: public HTTP version {actual} verified; changed={report["changed"][part]}')
                    break
            except OSError:
                pass
            time.sleep(2)
        else:
            raise RuntimeError(f'{part}: public version did not become {expected}')
    Path('build').mkdir(exist_ok=True)
    Path('build/deployment-result.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
