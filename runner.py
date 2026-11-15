"""Finding Antares, running programs, and reading the problems they report.

Nothing here touches the window, so it can be tested on its own.
"""
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

PROBLEM = re.compile(r"Problem on line (\d+)(?: of (.+?))?: (.*)")
# programs that draw on the screen need a real terminal window
LIVE = re.compile(r"\b(key|draw|clear)\s*\(")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW


def find_antares(configured=""):
    """The antares program to use: the one chosen in the settings, the one on
    the PATH, or the usual install places. None if there isn't one."""
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which("antares")
    if found:
        return found
    exe = "antares.exe" if os.name == "nt" else "antares"
    home = Path.home()
    for p in [home / ".cargo" / "bin" / exe, home / ".antares" / "bin" / exe,
              home / "AppData" / "Local" / "Programs" / "Antares" / exe, Path("/usr/local/bin") / exe]:
        if p.is_file():
            return str(p)
    return None


def antares_version(antares):
    try:
        r = subprocess.run([antares, "version"], capture_output=True, text=True, timeout=10,
                           creationflags=NO_WINDOW)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def parse_problem(text):
    """The first problem in Antares's output: (line, file or None, message), or None."""
    m = PROBLEM.search(text)
    if not m:
        return None
    return int(m.group(1)), m.group(2), m.group(3).strip()


def draws_on_screen(code):
    """Whether a program uses key(), draw() or clear(), which need a terminal."""
    for line in code.splitlines():
        if LIVE.search(line.split("#", 1)[0]):
            return True
    return False


class Run:
    """A running Antares program. Output arrives as ("out" | "err", text)
    items on .events, then ("done", exit_code). Write a line to its input
    with send()."""

    def __init__(self, cmd, cwd):
        self.events = queue.Queue()
        self.proc = subprocess.Popen(
            cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=NO_WINDOW, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.stopped = False
        self._readers = [
            threading.Thread(target=self._read, args=(self.proc.stdout, "out"), daemon=True),
            threading.Thread(target=self._read, args=(self.proc.stderr, "err"), daemon=True),
        ]
        for t in self._readers:
            t.start()
        threading.Thread(target=self._wait, daemon=True).start()

    def _read(self, stream, kind):
        # read whatever is there (not whole lines), so prompts from input("...")
        # show before the program waits for an answer
        fd = stream.fileno()
        decoder = __import__("codecs").getincrementaldecoder("utf-8")("replace")
        while True:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            text = decoder.decode(data)
            if text:
                self.events.put((kind, text.replace("\r\n", "\n")))
        rest = decoder.decode(b"", final=True)
        if rest:
            self.events.put((kind, rest))

    def _wait(self):
        code = self.proc.wait()
        for t in self._readers:
            t.join(timeout=2)
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            try:
                stream.close()
            except OSError:
                pass
        self.events.put(("done", code))

    def send(self, line):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.write((line + "\n").encode("utf-8"))
                self.proc.stdin.flush()
            except OSError:
                pass

    def stop(self):
        if self.proc.poll() is None:
            self.stopped = True
            try:
                self.proc.kill()
            except OSError:
                pass

    @property
    def running(self):
        return self.proc.poll() is None


def run_in_terminal(antares, path, cwd):
    """Runs a program in its own terminal window, for programs that draw on the
    screen with key(), draw() and clear(). The window stays open at the end."""
    if os.name == "nt":
        title = "Antares - " + Path(path).name
        subprocess.Popen(
            ["cmd", "/c", "start", title, "cmd", "/k", antares, path],
            cwd=cwd, creationflags=NO_WINDOW,
        )
    elif sys.platform == "darwin":
        script = f'tell application "Terminal" to do script "cd {shlex_quote(cwd)} && {shlex_quote(antares)} {shlex_quote(path)}"'
        subprocess.Popen(["osascript", "-e", script])
    else:
        for term in ["x-terminal-emulator", "gnome-terminal", "konsole", "xterm"]:
            if shutil.which(term):
                subprocess.Popen([term, "-e", f"{antares} {path}; read -p 'Press Enter to close'"], cwd=cwd)
                return
        raise OSError("couldn't find a terminal program")


def shlex_quote(s):
    import shlex
    return shlex.quote(s)
