"""Terminal colors and synchronous effects for the calculator game."""

import os
import re
import shutil
import sys
import time
from contextlib import contextmanager


RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_TEXT_TOKENS = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]|\r\n|[\r\n]|[^\S\r\n]+|[^\s\x1b]+|\x1b."
)


def paint(text, color):
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return str(text)
    return f"{color}{text}{RESET}"


def clear_screen():
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


@contextmanager
def _discard_keys_during_typing():
    """Temporarily consume terminal input so typed-ahead keys are ignored."""
    if not sys.stdin.isatty():
        yield
        return

    if os.name == "nt":
        import msvcrt

        def discard_pending():
            while msvcrt.kbhit():
                msvcrt.getwch()

        discard_pending()
        try:
            yield discard_pending
        finally:
            discard_pending()
        return

    import select
    import termios
    import tty

    descriptor = sys.stdin.fileno()
    previous_settings = termios.tcgetattr(descriptor)
    tty.setcbreak(descriptor)

    def discard_pending():
        while select.select([descriptor], [], [], 0)[0]:
            os.read(descriptor, 1)

    try:
        discard_pending()
        yield discard_pending
    finally:
        discard_pending()
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous_settings)


def _wrap_text(text, width):
    output = []
    pending_whitespace = []
    column = 0

    for token in _TEXT_TOKENS.findall(text):
        if token.startswith("\x1b"):
            output.append(token)
        elif token in {"\n", "\r", "\r\n"}:
            pending_whitespace.clear()
            output.append("\n")
            column = 0
        elif token.isspace():
            pending_whitespace.append(token)
        else:
            whitespace = "".join(pending_whitespace)
            if column and column + len(whitespace) + len(token) > width:
                output.append("\n")
                column = 0
            else:
                output.append(whitespace)
                column += len(whitespace)
            pending_whitespace.clear()

            for character in token:
                if column >= width:
                    output.append("\n")
                    column = 0
                output.append(character)
                column += 1

    return "".join(output)


def typewrite(text, delay=0.025, end="\n"):
    """Print text character by character, ignoring keys until it finishes."""
    width = max(1, shutil.get_terminal_size((80, 24)).columns - 1)
    wrapped_text = _wrap_text(str(text), width)
    with _discard_keys_during_typing() as discard_pending:
        for character in wrapped_text:
            sys.stdout.write(character)
            sys.stdout.flush()
            if delay > 0:
                time.sleep(delay)
            if discard_pending:
                discard_pending()
    sys.stdout.write(end)
    sys.stdout.flush()