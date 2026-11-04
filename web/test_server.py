"""Integration tests against an actual, unchanged executable JAR."""
import json
import os
from pathlib import Path
import re
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import Server


class BrowserGameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = Server(('127.0.0.1', 0), Path(os.environ['TEST_JAR']).resolve())
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        for game in cls.server.games.values():
            game.close()

    def call(self, path, body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-Game-Token'] = token
        request = Request(self.url + path, headers=headers,
                          data=json.dumps(body).encode() if body is not None else None)
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def wait(self, token, predicate):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            state = self.call('/api/game', token=token)
            if predicate(state):
                return state
            time.sleep(.05)
        self.fail('JAR output timed out: ' + str(state))

    def test_complete_game_and_isolation(self):
        token = self.call('/api/game', {})['token']
        other = self.call('/api/game', {})['token']
        for current in (token, other):
            state = self.wait(current, lambda s: 'Gegner (1=Greedy, 2=Perfect):' in s['output'] or '(0-8)' in s['output'])
            if 'Gegner (1=Greedy, 2=Perfect):' in state['output']:
                self.call('/api/move', {'move': 1}, current)
        initial = self.wait(token, lambda s: '(0-8)' in s['output'])
        self.wait(other, lambda s: '(0-8)' in s['output'])
        state = initial
        for _ in range(5):
            board = state['output'].rsplit('Where to put', 1)[0].splitlines()[-3:]
            move = int(re.search(r'\d', '\n'.join(board)).group())
            previous = state['output']
            self.call('/api/move', {'move': move}, token)
            state = self.wait(token, lambda s: s['finished'] or
                              (s['output'] != previous and s['output'].rstrip().endswith('(0-8):')))
            if state['finished']:
                break
        self.assertTrue(state['finished'])
        self.assertRegex(state['output'], r'winner|draw')
        self.assertNotIn('\x1b', state['output'])
        self.assertEqual(initial['output'], self.call('/api/game', token=other)['output'])
        with self.assertRaises(HTTPError) as error:
            self.call('/api/move', {'move': 9}, other)
        self.assertEqual(400, error.exception.code)
        with self.assertRaises(HTTPError) as error:
            self.call('/api/game', token='unknown')
        self.assertEqual(404, error.exception.code)


if __name__ == '__main__':
    unittest.main()
