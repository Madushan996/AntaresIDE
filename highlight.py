"""Finds the parts of Antares code to colour: comments, text, numbers,
keywords, built-in functions and the names of functions being defined.

tokens(code) gives (start, end, kind) for each part, as positions in the
code. It never fails, even on half-typed code: anything it doesn't
recognise is simply left uncoloured.
"""
import re

from help_data import BUILTINS

KEYWORDS = {
    "and", "as", "ask", "by", "change", "descend", "each", "else", "give", "in", "learn", "model",
    "not", "or", "repeat", "show", "skip", "stop", "to", "try", "use", "using", "when", "while",
    "with", "xor", "within",
}
CONSTANTS = {"yes", "no", "nothing"}

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUMBER = re.compile(r"0[xX][0-9A-Fa-f_]+|\d[\d_]*(\.\d+)?([eE][+-]?\d+)?")


def tokens(code):
    out = []
    i = 0
    n = len(code)
    prev_word = None  # to colour the name after `to`
    while i < n:
        c = code[i]
        if c == "#":
            j = code.find("\n", i)
            j = n if j < 0 else j
            out.append((i, j, "comment"))
            i = j
            prev_word = None
            continue
        if c == '"':
            i = _text(code, i, out)
            prev_word = None
            continue
        if c.isdigit():
            m = _NUMBER.match(code, i)
            out.append((i, m.end(), "number"))
            i = m.end()
            prev_word = None
            continue
        if c.isalpha() or c == "_":
            m = _WORD.match(code, i)
            w = m.group(0)
            kind = None
            if prev_word in ("to", "model", "learn"):
                kind = "define"
            elif w in KEYWORDS:
                kind = "keyword"
            elif w in CONSTANTS:
                kind = "constant"
            elif w in BUILTINS and _called(code, i, m.end()):
                kind = "builtin"
            if kind:
                out.append((i, m.end(), kind))
            prev_word = w
            i = m.end()
            continue
        if not c.isspace():
            prev_word = None
        i += 1
    return out


def _called(code, start, end):
    """Whether the name from start to end is called (followed by '(', spaces
    allowed) or used as a pipeline step (`-> sort`)."""
    k = end
    while k < len(code) and code[k] in " \t":
        k += 1
    if k < len(code) and code[k] == "(":
        return True
    return code[:start].rstrip().endswith("->")


def _text(code, i, out):
    """A text literal starting at i (the opening quote): text, with the code
    inside { } coloured as code. Returns where it ends."""
    n = len(code)
    start = i
    i += 1
    seg = start
    while i < n:
        c = code[i]
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if c == '"':
            out.append((seg, i + 1, "text"))
            return i + 1
        if c == "{":
            out.append((seg, i, "text"))
            # find the matching } (code inside may contain text with its own braces)
            depth = 1
            j = i + 1
            while j < n and depth:
                if code[j] == '"':
                    # text inside the braces
                    k = j + 1
                    while k < n and code[k] != '"':
                        k += 2 if code[k] == "\\" else 1
                    j = k + 1
                    continue
                if code[j] == "{":
                    depth += 1
                elif code[j] == "}":
                    depth -= 1
                j += 1
            inner = code[i + 1:j - 1] if depth == 0 else code[i + 1:j]
            out.append((i, i + 1, "interp"))
            for s, e, k in tokens(inner):
                out.append((i + 1 + s, i + 1 + e, k))
            if depth == 0:
                out.append((j - 1, j, "interp"))
            i = j
            seg = i
            continue
        i += 1
    out.append((seg, n, "text"))  # unfinished text
    return n


def offsets_to_index(code):
    """A function turning a position in the code into a Tk "line.column" index."""
    starts = [0]
    for k, ch in enumerate(code):
        if ch == "\n":
            starts.append(k + 1)
    import bisect

    def index(pos):
        line = bisect.bisect_right(starts, pos) - 1
        return f"{line + 1}.{pos - starts[line]}"

    return index
