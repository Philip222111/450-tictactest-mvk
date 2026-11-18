"""Read GitHub release metadata; never treat a bare tag or draft as a release."""
import json
import re
import subprocess
import sys


def validate_tag(tag):
    if not re.fullmatch(r'v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)', tag):
        raise ValueError('Expected vMAJOR.MINOR.PATCH without leading zeroes')


def published_release(tag):
    validate_tag(tag)
    result = subprocess.run(
        ['gh', 'release', 'view', tag, '--json', 'tagName,isDraft,publishedAt'],
        capture_output=True, text=True, check=True, timeout=30)
    release = json.loads(result.stdout)
    if release.get('tagName') != tag or release.get('isDraft') is not False or not release.get('publishedAt'):
        raise ValueError('Requested release is not published')
    return release


if __name__ == '__main__':
    published_release(sys.argv[1])
