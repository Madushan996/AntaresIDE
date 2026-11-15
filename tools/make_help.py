"""Makes help_data.py (the help panel's reference) from the Antares manual.

  python tools/make_help.py [path/to/manual.md]

By default it reads the manual of the Antares checkout next to this folder
(..\\Antares\\docs\\src\\manual.md). Run it again when Antares gains functions.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DEFAULT = HERE.parent / "Antares" / "docs" / "src" / "manual.md"

# Statements and keywords: what the help panel says about them.
STATEMENTS = [
    ("show", "show a, b", "Prints values on one line, separated by spaces."),
    ("when", "when cond { } else when cond { } else { }", "Runs a block only when a condition is yes; else when and else handle the other cases."),
    ("else", "else { }", "The block a when (or try) runs otherwise."),
    ("repeat", "repeat n { }  /  repeat n as i { }", "Runs a block n times; with as i, i counts 1, 2, ... n."),
    ("each", "each x in list { }", "Runs a block once for every item of a list, letter of a text or field of a map."),
    ("while", "while cond { }", "Repeats a block while a condition stays yes."),
    ("stop", "stop", "Leaves the loop it is in, at once."),
    ("skip", "skip", "Jumps to the next round of the loop it is in."),
    ("to", "to name(a, b) = expr  /  to name(a) { }", "Defines a function. A block function gives back its last line."),
    ("give", "give value", "Leaves a function at once, giving back the value."),
    ("change", "change name = value", "Changes a variable that lives outside the function (also change name += value)."),
    ("try", "try { } else problem { }", "Runs a block; if anything in it fails, runs the else block instead, with the message."),
    ("use", "use \"file\"", "Runs another file (file.ant, next to this one) once, making its functions available."),
    ("learn", "learn w = value", "Makes a value that learning (descend) may adjust."),
    ("descend", "descend loss by rate [using adam]", "Adjusts every learnable value the loss depends on, to make the loss smaller."),
    ("model", "model name = \"anthropic:model\" [with {system: \"...\"}]", "Declares an AI model to ask questions."),
    ("ask", "ask model \"question\" [as number | yes/no | list]", "Asks an AI model; the answer is text, or the kind after as."),
    ("within", "name = value within lo to hi  /  to f(x within lo to hi)", "Keeps a variable's numbers (or a function input) from lo to hi; anything else is a problem."),
    ("and", "a and b", "yes when both are yes."),
    ("or", "a or b", "yes when at least one is yes."),
    ("not", "not a", "Turns yes into no and no into yes."),
    ("xor", "a xor b", "For integers: the bits set in one but not both."),
    ("in", "each x in list", "Part of each."),
    ("as", "repeat n as i  /  ask m \"q\" as number", "Names the counter of repeat, or the kind of an answer."),
    ("by", "descend loss by rate", "Part of descend: the learning rate."),
    ("using", "descend loss by rate using adam", "Part of descend: sgd or adam."),
    ("with", "model m = \"...\" with {system: \"...\"}", "Part of model: its settings."),
    ("yes", "yes", "The true yes/no value."),
    ("no", "no", "The false yes/no value."),
    ("nothing", "nothing", "The value that means 'no value'."),
]


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    text = src.read_text(encoding="utf-8")
    start = text.index("# Built-in Function Reference")
    end = text.index("\n# ", start + 10)
    part = text[start:end]
    version = re.search(r"This manual describes \*\*Antares ([\d.]+)\*\*", text).group(1)
    builtins = {}
    group = ""
    for line in part.splitlines():
        if line.startswith("## "):
            group = line[3:].strip()
            continue
        m = re.match(r"\|\s*(`.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m or line.startswith("|---") or "Function" in m.group(1):
            continue
        cell, desc = m.group(1), m.group(2)
        sigs = re.findall(r"`([^`]+)`", cell)
        desc = re.sub(r"`([^`]+)`", r"\1", desc)
        for sig in sigs:
            name = re.match(r"[a-z_]+", sig)
            if not name:
                continue
            n = name.group(0)
            if n in builtins:
                # a second form of the same function (argmax(x) and argmax(row, first, last))
                builtins[n]["sig"] += "  /  " + sig
                if desc not in builtins[n]["desc"]:
                    builtins[n]["desc"] = builtins[n]["desc"].rstrip(".") + ". " + desc
            else:
                builtins[n] = {"group": group, "sig": sig, "desc": desc}
    out = HERE / "help_data.py"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write('"""The help panel\'s reference. Made by tools/make_help.py from the Antares\n')
        f.write(f'manual (version {version}); don\'t edit by hand."""\n\n')
        f.write(f"VERSION = {version!r}\n\n")
        f.write("BUILTINS = " + json.dumps(builtins, indent=4, ensure_ascii=False) + "\n\n")
        f.write("STATEMENTS = " + json.dumps({k: {"sig": s, "desc": d} for k, s, d in STATEMENTS}, indent=4, ensure_ascii=False) + "\n")
    print(f"Wrote {out}: {len(builtins)} built-in functions, {len(STATEMENTS)} statements and keywords (Antares {version})")


if __name__ == "__main__":
    main()
