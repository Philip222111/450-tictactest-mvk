"""CI and manual deployment: consumes release-assets, never builds or runs IaC."""
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.request import urlopen


def aws(*args):
    result = subprocess.run(['aws', *args, '--output', 'json'], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main():
    tag = os.environ['TAG']
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Invalid tag')
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
    for part, path in [('backend', '/backend-version.json'), ('frontend', '/version.json')]:
        expected = report['versions'][part]
        for attempt in range(20):
            try:
                with urlopen(os.environ['APP_URL'].rstrip('/') + path, timeout=4) as response:
                    actual = json.load(response)['version']
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
