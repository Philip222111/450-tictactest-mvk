"""Start the built/downloaded JAR and play a complete game through stdin."""

import queue
import subprocess
import sys
import threading
import time


def smoke(jar):
    # Send one move per prompt: HumanPlayer creates a scanner each turn.
    process = subprocess.Popen(
        ["java", "-jar", str(jar)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8",
    )
    lines = queue.Queue()
    threading.Thread(
        target=lambda: [lines.put(line) for line in process.stdout],
        daemon=True,
    ).start()
    moves = iter(["0", "4", "8"])
    transcript = ""
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline:
            try:
                line = lines.get(timeout=0.2)
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue
            transcript += line
            if "(0-8):" in line:
                process.stdin.write(next(moves) + "\n")
                process.stdin.flush()
        if process.poll() is None:
            raise RuntimeError("JAR did not finish within 30 seconds")
        if process.returncode != 0 or "winner is: CROSS" not in transcript:
            raise RuntimeError("Game failed:\n" + transcript)
        print(transcript)
        print("JAR smoke test passed: human wins with 0, 4, 8.")
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()


if __name__ == "__main__":
    smoke(sys.argv[1])
