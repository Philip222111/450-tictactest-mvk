"""Run only downloaded release assets on two separate localhost ports."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import sys
import time
import zipfile


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--run-jar':
        result = subprocess.run([os.environ.get('JAVA', 'java'), '-Xmx48m', '-jar', sys.argv[2]])
        # Windows ConPTY otherwise closes before ttyd flushes the final board.
        time.sleep(1)
        raise SystemExit(result.returncode)
    parser = argparse.ArgumentParser()
    parser.add_argument('--jar', type=Path, required=True)
    parser.add_argument('--frontend', type=Path, required=True)
    parser.add_argument('--ttyd', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--console-port', type=int, default=7681)
    args = parser.parse_args()
    with zipfile.ZipFile(args.jar) as jar:
        version = re.search(r'^Implementation-Version: (\S+)', jar.read('META-INF/MANIFEST.MF').decode(), re.M)[1]
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/config.js':
                data = ('window.TICTACTEST = ' + json.dumps({
                    'consoleUrl': f'http://localhost:{args.console_port}/terminal/',
                    'backendVersionUrl': f'http://localhost:{args.port}/backend-version.json'}) + ';').encode()
                mime = 'application/javascript'
            elif self.path == '/backend-version.json':
                data, mime = json.dumps({'version': version}).encode(), 'application/json'
            else:
                return super().do_GET()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    with tempfile.TemporaryDirectory() as folder:
        with zipfile.ZipFile(args.frontend) as archive:
            archive.extractall(folder)
        process = subprocess.Popen([str(args.ttyd.resolve()), '-i', '127.0.0.1', '-p', str(args.console_port),
                                    '-W', '-m', '8', '-b', '/terminal', sys.executable,
                                    str(Path(__file__).resolve()), '--run-jar', str(args.jar.resolve())])
        server = ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(Handler, directory=folder))
        print(f'Frontend: http://localhost:{args.port} | Terminal: http://localhost:{args.console_port}/terminal/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            process.terminate()
            process.wait(timeout=10)


if __name__ == '__main__':
    main()
