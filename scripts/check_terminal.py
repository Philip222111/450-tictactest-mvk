"""Real ttyd/WebSocket smoke test; pip install websocket-client for this check."""
import json
import sys
import time
from urllib.request import urlopen
from websocket import create_connection


def play(base):
    with urlopen(base.rstrip('/') + '/terminal/token', timeout=10) as response:
        token = json.load(response)['token']
    ws = create_connection(base.replace('http', 'ws', 1).rstrip('/') + '/terminal/ws',
                           subprotocols=['tty'], origin=base.rstrip('/'), timeout=10)
    try:
        ws.send(json.dumps({'AuthToken': token, 'columns': 80, 'rows': 24}))
        output = ''
        moves = iter(['0', '4', '8'])
        prompts = 0
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            data = ws.recv()
            if not data: break
            data = data.decode('utf-8', errors='replace') if isinstance(data, bytes) else data
            if data[0] != '0': continue
            output += data[1:]
            if output.count('(0-8):') > prompts:
                prompts += 1
                ws.send_binary(b'0' + (next(moves) + '\r').encode())
            if 'winner is: CROSS' in output:
                print('ttyd PTY/WebSocket: complete game passed (0, 4, 8).')
                return
        raise RuntimeError('No completed game: ' + output)
    finally:
        ws.close()


if __name__ == '__main__':
    play(sys.argv[1])
