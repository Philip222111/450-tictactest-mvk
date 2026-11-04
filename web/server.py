"""Browser bridge for the unchanged console JAR. Python standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

class Game:
    def __init__(self, jar):
        self.lock = threading.Lock()
        self.output = ""
        self.touched = time.monotonic()
        self.process = subprocess.Popen([os.environ.get("JAVA", "java"), "-Xmx48m", "-jar", str(jar)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, bufsize=0)
        threading.Thread(target=self.read, daemon=True).start()

    def read(self):
        import codecs
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        while chunk := self.process.stdout.read(1024):
            with self.lock:
                self.output = (self.output + decoder.decode(chunk))[-32768:]

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()

class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, jar):
        super().__init__(address, Handler)
        self.jar = jar
        self.games = {}
        self.lock = threading.Lock()
        threading.Thread(target=self.reap, daemon=True).start()

    def reap(self):
        while True:
            time.sleep(10)
            with self.lock:
                for token, game in list(self.games.items()):
                    if time.monotonic() - game.touched > 300:
                        game.close()
                        del self.games[token]

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, value, mime="application/json"):
        data = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            return self.reply(200, Path(__file__).with_name("index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/health":
            return self.reply(200, {"ok": self.server.jar.is_file()})
        if self.path != "/api/game":
            return self.reply(404, {"error": "Nicht gefunden"})
        with self.server.lock:
            game = self.server.games.get(self.headers.get("X-Game-Token"))
            if not game:
                return self.reply(404, {"error": "Spiel abgelaufen. Neues Spiel starten."})
            game.touched = time.monotonic()
            with game.lock:
                return self.reply(200, {"output": ANSI.sub("", game.output), "finished": game.process.poll() is not None})

    def do_POST(self):
        # Only same-origin browser requests with JSON; no cross-origin CORS support.
        if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            return self.reply(403, {"error": "Fremde Herkunft"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 128 or self.headers.get("Content-Type") != "application/json":
                raise ValueError()
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, json.JSONDecodeError):
            return self.reply(400, {"error": "Ungueltige Anfrage"})
        with self.server.lock:
            token = self.headers.get("X-Game-Token")
            if self.path == "/api/game":
                if token in self.server.games:
                    self.server.games.pop(token).close()
                if len(self.server.games) >= 8:
                    return self.reply(429, {"error": "Alle Spielplaetze belegt. Spaeter erneut versuchen."})
                token = secrets.token_urlsafe(32)
                self.server.games[token] = Game(self.server.jar)
                return self.reply(201, {"token": token})
            if self.path != "/api/move":
                return self.reply(404, {"error": "Nicht gefunden"})
            game = self.server.games.get(token)
            move = body.get("move")
            if not game:
                return self.reply(404, {"error": "Spiel abgelaufen"})
            if type(move) is not int or not 0 <= move <= 8:
                return self.reply(400, {"error": "Position muss 0 bis 8 sein"})
            try:
                game.process.stdin.write(f"{move}\n".encode())
                game.process.stdin.flush()
                game.touched = time.monotonic()
            except (BrokenPipeError, OSError):
                return self.reply(409, {"error": "Spiel beendet"})
            self.reply(200, {"ok": True})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if not args.jar.is_file():
        parser.error("JAR nicht gefunden")
    server = Server((args.host, args.port), args.jar.resolve())
    print(f"Web-Konsole: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        with server.lock:
            for game in server.games.values():
                game.close()
