"""Real ttyd/WebSocket smoke test; pip install websocket-client for this check."""
import json
import argparse
import sys
import time
from urllib.request import urlopen
from websocket import create_connection


def play(base, opponent='greedy'):
    with urlopen(base.rstrip('/') + '/terminal/token', timeout=10) as response:
        token = json.load(response)['token']
    ws = create_connection(base.replace('http', 'ws', 1).rstrip('/') + '/terminal/ws',
                           subprotocols=['tty'], origin=base.rstrip('/'), timeout=10)
    try:
        ws.send(json.dumps({'AuthToken': token, 'columns': 80, 'rows': 24}))
        output = ''
        moves = iter(['0', '4', '8'] if opponent == 'greedy' else ['0', '1', '3'])
        winner = 'CROSS' if opponent == 'greedy' else 'CIRCLE'
        selected = False
        prompts = 0
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            data = ws.recv()
            if not data: break
            data = data.decode('utf-8', errors='replace') if isinstance(data, bytes) else data
            if data[0] != '0': continue
            output += data[1:]
            if 'Gegner (1=Greedy, 2=Perfect):' in output and not selected:
                ws.send_binary(b'0' + (b'1\r' if opponent == 'greedy' else b'2\r'))
                selected = True
            if output.count('(0-8):') > prompts:
                if opponent == 'perfect' and not selected:
                    raise RuntimeError('This release has no opponent menu')
                prompts += 1
                ws.send_binary(b'0' + (next(moves) + '\r').encode())
            if 'winner is: ' + winner in output:
                print(f'ttyd PTY/WebSocket: {opponent} selected, complete game passed ({winner} wins).')
                return
        raise RuntimeError('No completed game: ' + output)
    finally:
        ws.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('base')
    parser.add_argument('--opponent', choices=['greedy', 'perfect'], default='greedy')
    args = parser.parse_args()
    play(args.base, args.opponent)
