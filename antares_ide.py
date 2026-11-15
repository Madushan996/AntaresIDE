"""Antares IDE: a small, friendly place to write and run Antares programs.

  python antares_ide.py [file.ant]

Write code on the left, press Run (F5), and see what it prints underneath.
If something goes wrong, the line is marked and the problem explained. The
help panel on the right describes every statement and built-in function.
"""
import json
import os
import re
import sys
import tempfile
import time
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import highlight
import runner
from help_data import BUILTINS, STATEMENTS, VERSION as MANUAL_VERSION

APP = "Antares IDE"
IDE_VERSION = "1.0.1"
HERE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
SETTINGS_FILE = Path.home() / ".antares_ide.json"
SCRATCH = Path(tempfile.gettempdir()) / "antares_ide"
INSTALL_WINDOWS = "irm https://raw.githubusercontent.com/Madushan996/Antares-Programming-Language/main/install.ps1 | iex"
INSTALL_UNIX = "curl -fsSL https://raw.githubusercontent.com/Madushan996/Antares-Programming-Language/main/install.sh | sh"
BOOK_URL = "https://github.com/Madushan996/Antares-Programming-Language/blob/main/docs/Learn_Antares.pdf"
MANUAL_URL = "https://github.com/Madushan996/Antares-Programming-Language/blob/main/docs/Antares_Language_Reference.pdf"

WELCOME = '''# Welcome to Antares!
#
# This is your code. Press the green Run button
# (or F5) to run it. What it shows appears below.
#
# Lines starting with # are comments: notes for
# people, which Antares ignores.

name = "world"
show "Hello, {name}!"

repeat 3 as n {
    show "{n} times 7 is {n * 7}"
}

# Try changing the name above, then run it again.
# The help panel on the right explains every word.
# Click on a word and press F1 to see its help.
'''

NEW_FILE = '''# My program

show "Hello!"
'''

THEMES = {
    "light": {
        "bg": "#ffffff", "fg": "#1f2430", "gutter": "#f4f5f8", "gutter_fg": "#9aa1b2", "curline": "#f3f6fb",
        "select": "#cfe0fb", "cursor": "#1f2430", "panel": "#f7f8fa", "panel_fg": "#1f2430", "border": "#dfe2e8",
        "comment": "#8a93a6", "text": "#2e7d32", "interp": "#c2410c", "number": "#9c27b0", "keyword": "#c2410c",
        "constant": "#b45309", "builtin": "#1565c0", "define": "#0f766e",
        "out": "#1f2430", "err": "#c62828", "info": "#6b7280", "input": "#1565c0", "ok": "#2e7d32",
        "problem_bg": "#fde2e1", "find_bg": "#fff3a3", "accent": "#e8590c",
    },
    "dark": {
        "bg": "#1e2230", "fg": "#d8dcea", "gutter": "#191c28", "gutter_fg": "#5c6378", "curline": "#252a3a",
        "select": "#34405e", "cursor": "#ffffff", "panel": "#191c28", "panel_fg": "#d8dcea", "border": "#2c3244",
        "comment": "#6c7489", "text": "#a8e0a0", "interp": "#ffb06b", "number": "#e3b3ff", "keyword": "#ff9a62",
        "constant": "#ffd59a", "builtin": "#8cc4ff", "define": "#7ee0d0",
        "out": "#d8dcea", "err": "#ff8a80", "info": "#8b93a7", "input": "#8cc4ff", "ok": "#a8e0a0",
        "problem_bg": "#5a2a2e", "find_bg": "#5b5320", "accent": "#ff8a3d",
    },
}

# Plain-words advice for the problems beginners meet most.
HINTS = [
    ("I don't know what", "Check the spelling. A name must be given a value (name = ...) before it is used."),
    ('missing its closing "', 'Every text needs a closing double quote ".'),
    ("missing its closing '}'", "Every { needs a matching }. Look for a block that was never closed."),
    ("out of range", "Positions start at 0, so in a list of 3 items the last one is at position 2."),
    ("between a text and a number", "Turn text into a number with number(...) before doing arithmetic with it."),
    ("isn't a number", 'number(...) only works on text that is a number, like "42".'),
    ("I need a yes or no", "when and while need a comparison, such as x > 0 or name == \"Ana\"."),
    ("but was given", "Check how many values you give the function, between its brackets."),
    ("but found '='", "To compare two values, use == (two equals signs). One = gives a variable a value."),
    ("only holds numbers from", "A value broke a range set with within. Check the value, or the range."),
    ("has no '", 'That map doesn\'t have the field. Check first with has(map, "field").'),
    ("I didn't expect the end of the file", "Something at the end of the program is unfinished, such as a sum like 1 +."),
    ("I expected", "The shape of this line isn't quite right. Compare it with an example in the help panel."),
]


def hint_for(message):
    for part, hint in HINTS:
        if part in message:
            return hint
    return None


# ---------------------------------------------------------------------------
# Settings


class Settings:
    DEFAULTS = {"theme": "light", "font_size": 12, "recent": [], "geometry": "1280x800", "antares": "", "last_file": ""}

    def __init__(self):
        self.data = dict(self.DEFAULTS)
        try:
            self.data.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass

    def __getitem__(self, k):
        return self.data.get(k, self.DEFAULTS.get(k))

    def __setitem__(self, k, v):
        self.data[k] = v

    def save(self):
        try:
            SETTINGS_FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def add_recent(self, path):
        rec = [p for p in self["recent"] if p != path]
        self["recent"] = ([path] + rec)[:10]


def mono_font():
    available = set(tkfont.families())
    for f in ["Cascadia Mono", "Cascadia Code", "Consolas", "JetBrains Mono", "Menlo", "DejaVu Sans Mono", "Courier New"]:
        if f in available:
            return f
    return "TkFixedFont"


def ui_font():
    available = set(tkfont.families())
    for f in ["Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu", "DejaVu Sans"]:
        if f in available:
            return f
    return "TkDefaultFont"


# ---------------------------------------------------------------------------
# The editor


class Editor(tk.Frame):
    TOKEN_KINDS = ["comment", "text", "interp", "number", "keyword", "constant", "builtin", "define"]
    PAIRS = {"(": ")", "[": "]", "{": "}"}

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.font = tkfont.Font(family=mono_font(), size=app.settings["font_size"])
        self.gutter = tk.Canvas(self, width=48, highlightthickness=0, bd=0)
        self.text = tk.Text(self, wrap="none", undo=True, autoseparators=True, maxundo=-1, font=self.font,
                            bd=0, highlightthickness=0, padx=10, pady=6, tabs=(self.font.measure("    "),))
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self._yview)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self.hbar.set)
        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.vbar.grid(row=0, column=2, sticky="ns")
        self.hbar.grid(row=1, column=1, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self._hl_job = None
        self.problem_line = None
        self.popup = None
        self._popup_nav = False
        t = self.text
        t.bind("<<Modified>>", self._on_modified)
        t.bind("<KeyRelease>", self._on_key_release)
        t.bind("<ButtonRelease-1>", lambda e: (self._update_curline(), self.hide_popup(), self.app.update_position()))
        t.bind("<Configure>", lambda e: self.redraw_gutter())
        t.bind("<Return>", self._on_return)
        t.bind("<Tab>", self._on_tab)
        t.bind("<Shift-Tab>", self._on_shift_tab)
        if sys.platform.startswith("linux"):
            t.bind("<ISO_Left_Tab>", self._on_shift_tab)
        t.bind("<BackSpace>", self._on_backspace)
        t.bind("<Key>", self._on_key)
        t.bind("<Escape>", lambda e: self.hide_popup())
        t.bind("<Up>", lambda e: self._popup_move(-1))
        t.bind("<Down>", lambda e: self._popup_move(1))
        t.bind("<FocusOut>", lambda e: self.after(150, self._maybe_hide_popup))
        t.bind("<Control-space>", lambda e: (self.show_completions(force=True), "break")[1])
        t.bind("<Control-slash>", lambda e: (self.toggle_comment(), "break")[1])
        t.bind("<MouseWheel>", lambda e: self.after(1, self.redraw_gutter))
        t.bind("<Control-MouseWheel>", lambda e: (self.app.zoom(1 if e.delta > 0 else -1), "break")[1])
        self.apply_theme()

    # ----- look -----

    def apply_theme(self):
        th = self.app.theme
        self.text.configure(bg=th["bg"], fg=th["fg"], insertbackground=th["cursor"], selectbackground=th["select"],
                            selectforeground=th["fg"], inactiveselectbackground=th["select"])
        self.gutter.configure(bg=th["gutter"])
        self.configure(bg=th["gutter"])
        for k in self.TOKEN_KINDS:
            self.text.tag_configure(k, foreground=th[k])
        self.text.tag_configure("comment", font=tkfont.Font(family=self.font.cget("family"), size=self.font.cget("size"), slant="italic"))
        self.text.tag_configure("curline", background=th["curline"])
        self.text.tag_configure("problem", background=th["problem_bg"])
        self.text.tag_configure("found", background=th["find_bg"])
        self.text.tag_raise("sel")
        self.redraw_gutter()

    def set_font_size(self, size):
        self.font.configure(size=size)
        self.text.configure(tabs=(self.font.measure("    "),))
        self.apply_theme()

    # ----- content -----

    def get(self):
        return self.text.get("1.0", "end-1c")

    def set(self, code):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", code)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.text.mark_set("insert", "1.0")
        self.text.see("1.0")
        self.clear_problem()
        self.highlight_now()
        self._update_curline()
        self.app.update_position()

    # ----- colouring -----

    def _on_modified(self, _e=None):
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        self.app.mark_dirty()
        self.clear_problem()
        if self._hl_job:
            self.after_cancel(self._hl_job)
        self._hl_job = self.after(120, self.highlight_now)
        self.redraw_gutter()

    def highlight_now(self):
        self._hl_job = None
        code = self.get()
        for k in self.TOKEN_KINDS:
            self.text.tag_remove(k, "1.0", "end")
        if len(code) > 400_000:
            return
        index = highlight.offsets_to_index(code)
        for s, e, kind in highlight.tokens(code):
            self.text.tag_add(kind, index(s), index(e))
        self.text.tag_raise("sel")

    def _update_curline(self):
        self.text.tag_remove("curline", "1.0", "end")
        self.text.tag_add("curline", "insert linestart", "insert linestart+1l")
        self.text.tag_lower("curline")

    # ----- line numbers -----

    def _on_yscroll(self, first, last):
        self.vbar.set(first, last)
        self.redraw_gutter()

    def _yview(self, *args):
        self.text.yview(*args)
        self.redraw_gutter()

    def redraw_gutter(self):
        g = self.gutter
        g.delete("all")
        th = self.app.theme
        last = int(self.text.index("end-1c").split(".")[0])
        width = self.font.measure("0" * max(3, len(str(last)))) + 22
        g.configure(width=width)
        i = self.text.index("@0,0")
        while True:
            d = self.text.dlineinfo(i)
            if d is None:
                break
            line = int(i.split(".")[0])
            color = th["err"] if line == self.problem_line else th["gutter_fg"]
            if line == self.problem_line:
                g.create_oval(4, d[1] + d[3] / 2 - 4, 12, d[1] + d[3] / 2 + 4, fill=th["err"], outline="")
            g.create_text(width - 8, d[1] + 1, anchor="ne", text=str(line), fill=color, font=self.font)
            nxt = self.text.index(f"{i}+1line")
            if nxt == i:
                break
            i = nxt

    # ----- problems -----

    def mark_problem(self, line):
        self.clear_problem()
        last = int(self.text.index("end-1c").split(".")[0])
        line = max(1, min(line, last))
        self.problem_line = line
        self.text.tag_add("problem", f"{line}.0", f"{line}.0+1line")
        self.text.mark_set("insert", f"{line}.0 lineend")
        self.text.see(f"{line}.0")
        self._update_curline()
        self.redraw_gutter()
        self.app.update_position()

    def clear_problem(self):
        if self.problem_line is not None:
            self.problem_line = None
            self.text.tag_remove("problem", "1.0", "end")
            self.redraw_gutter()

    # ----- typing helpers -----

    def _on_key_release(self, e):
        self._update_curline()
        self.app.update_position()
        if e.keysym in ("Up", "Down", "Return", "Tab", "Escape", "Left", "Right", "Home", "End", "Prior", "Next"):
            return
        if e.char and (e.char.isalnum() or e.char == "_"):
            self.show_completions()
        elif e.keysym not in ("Shift_L", "Shift_R", "Control_L", "Control_R"):
            self.hide_popup()
        if e.char == "(":
            self.app.show_signature(self.word_before("insert-1c"))

    def _on_key(self, e):
        t = self.text
        ch = e.char
        if not ch or e.state & 0x4:  # nothing typed, or Control held
            return
        if ch in self.PAIRS:
            nxt = t.get("insert")
            if nxt in ("", "\n", " ", ")", "]", "}", ","):
                if t.tag_ranges("sel"):
                    return
                t.insert("insert", ch + self.PAIRS[ch])
                t.mark_set("insert", "insert-1c")
                return "break"
        if ch in (")", "]", "}") and t.get("insert") == ch:
            t.mark_set("insert", "insert+1c")
            return "break"
        if ch == "}":
            # a closing brace on a line of its own goes back one indent
            before = t.get("insert linestart", "insert")
            if before.strip() == "" and len(before) >= 4:
                t.delete("insert-4c", "insert")

    def _on_backspace(self, e):
        t = self.text
        if t.tag_ranges("sel"):
            return
        prev, nxt = t.get("insert-1c"), t.get("insert")
        if prev in self.PAIRS and self.PAIRS[prev] == nxt:
            t.delete("insert-1c", "insert+1c")
            return "break"
        before = t.get("insert linestart", "insert")
        if before and before.strip() == "" and len(before) % 4 == 0:
            t.delete("insert-4c", "insert")
            return "break"

    def _on_return(self, e):
        if self.popup and self._popup_nav:
            self.accept_completion()
            return "break"
        self.hide_popup()
        t = self.text
        line = t.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group(0)
        opens = line.rstrip().endswith("{")
        t.edit_separator()
        if opens and t.get("insert") == "}":
            t.insert("insert", "\n" + indent + "    " + "\n" + indent)
            t.mark_set("insert", "insert-1l lineend")
        else:
            t.insert("insert", "\n" + indent + ("    " if opens else ""))
        t.see("insert")
        self._update_curline()
        self.redraw_gutter()
        return "break"

    def _selected_lines(self):
        t = self.text
        if t.tag_ranges("sel"):
            first = int(t.index("sel.first").split(".")[0])
            last_idx = t.index("sel.last")
            last = int(last_idx.split(".")[0])
            if last_idx.endswith(".0") and last > first:
                last -= 1
            return first, last
        n = int(t.index("insert").split(".")[0])
        return n, n

    def _on_tab(self, e):
        if self.popup:
            self.accept_completion()
            return "break"
        t = self.text
        if t.tag_ranges("sel") and t.index("sel.first").split(".")[0] != t.index("sel.last").split(".")[0]:
            a, b = self._selected_lines()
            for n in range(a, b + 1):
                t.insert(f"{n}.0", "    ")
        else:
            t.insert("insert", "    ")
        return "break"

    def _on_shift_tab(self, e):
        t = self.text
        a, b = self._selected_lines()
        for n in range(a, b + 1):
            lead = t.get(f"{n}.0", f"{n}.4")
            k = len(lead) - len(lead.lstrip(" "))
            if k:
                t.delete(f"{n}.0", f"{n}.{k}")
        return "break"

    def toggle_comment(self):
        t = self.text
        a, b = self._selected_lines()
        lines = [t.get(f"{n}.0", f"{n}.end") for n in range(a, b + 1)]
        filled = [l for l in lines if l.strip()]
        commented = filled and all(l.lstrip().startswith("#") for l in filled)
        t.edit_separator()
        for n, l in zip(range(a, b + 1), lines):
            if not l.strip():
                continue
            k = len(l) - len(l.lstrip())
            if commented:
                rest = l[k + 1:]
                rest = rest[1:] if rest.startswith(" ") else rest
                t.delete(f"{n}.0", f"{n}.end")
                t.insert(f"{n}.0", l[:k] + rest)
            else:
                t.insert(f"{n}.{k}", "# ")
        t.edit_separator()

    def word_before(self, index="insert"):
        t = self.text
        line = t.get(f"{index} linestart", index)
        m = re.search(r"[A-Za-z_][A-Za-z0-9_]*$", line)
        return m.group(0) if m else ""

    def word_at(self, index="insert"):
        t = self.text
        line = t.get(f"{index} linestart", f"{index} lineend")
        col = int(t.index(index).split(".")[1])
        for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", line):
            if m.start() <= col <= m.end():
                return m.group(0)
        return ""

    # ----- completion -----

    def _candidates(self, prefix):
        words = set(highlight.KEYWORDS) | set(highlight.CONSTANTS) | set(BUILTINS)
        code = self.get()
        counts = {}
        for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code):
            counts[w] = counts.get(w, 0) + 1
        for w, c in counts.items():
            if w != prefix or c > 1:
                words.add(w)
        return sorted(w for w in words if w.startswith(prefix) and w != prefix)

    def show_completions(self, force=False):
        t = self.text
        # not inside comments or text
        tags = t.tag_names("insert-1c")
        if "comment" in tags or ("text" in tags and not force):
            self.hide_popup()
            return
        prefix = self.word_before()
        if len(prefix) < (1 if force else 2):
            self.hide_popup()
            return
        cands = self._candidates(prefix)[:12]
        if not cands:
            self.hide_popup()
            return
        bbox = t.bbox("insert")
        if not bbox:
            return
        th = self.app.theme
        if not self.popup:
            self.popup = tk.Toplevel(self)
            self.popup.wm_overrideredirect(True)
            self.popup_list = tk.Listbox(self.popup, height=6, activestyle="none", bd=1, relief="solid",
                                         font=self.font, exportselection=False)
            self.popup_list.pack(fill="both", expand=True)
            self.popup_list.bind("<Double-Button-1>", lambda e: self.accept_completion())
        lb = self.popup_list
        lb.configure(bg=th["panel"], fg=th["panel_fg"], selectbackground=th["select"], selectforeground=th["fg"],
                     highlightthickness=0)
        lb.delete(0, "end")
        for c in cands:
            lb.insert("end", c + ("( )" if c in BUILTINS else ""))
        lb.selection_set(0)
        lb.configure(height=min(8, len(cands)), width=max(len(c) for c in cands) + 5)
        x = t.winfo_rootx() + bbox[0]
        y = t.winfo_rooty() + bbox[1] + bbox[3] + 2
        self.popup.wm_geometry(f"+{x}+{y}")
        self.popup.deiconify()
        self.popup.lift()
        self._popup_prefix = prefix
        self._popup_items = cands
        self._popup_nav = False
        self.app.show_help_quiet(cands[0])

    def _popup_move(self, d):
        if not self.popup:
            return
        lb = self.popup_list
        cur = lb.curselection()
        i = (cur[0] if cur else 0) + d
        i = max(0, min(i, lb.size() - 1))
        lb.selection_clear(0, "end")
        lb.selection_set(i)
        lb.see(i)
        self._popup_nav = True
        self.app.show_help_quiet(self._popup_items[i])
        return "break"

    def accept_completion(self):
        if not self.popup:
            return
        cur = self.popup_list.curselection()
        word = self._popup_items[cur[0] if cur else 0]
        t = self.text
        t.delete(f"insert-{len(self._popup_prefix)}c", "insert")
        if word in BUILTINS and t.get("insert") != "(":
            t.insert("insert", word + "()")
            t.mark_set("insert", "insert-1c")
            self.app.show_signature(word)
        else:
            t.insert("insert", word)
        self.hide_popup()

    def _maybe_hide_popup(self):
        if self.popup and self.focus_get() not in (self.text, self.popup_list):
            self.hide_popup()

    def hide_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None


# ---------------------------------------------------------------------------
# Panels


class OutputPanel(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        head = tk.Frame(self)
        head.pack(fill="x")
        self.title = tk.Label(head, text="Output", font=(ui_font(), 10, "bold"), anchor="w", padx=10, pady=4)
        self.title.pack(side="left")
        self.clear_btn = ttk.Button(head, text="Clear", command=self.clear, style="Small.TButton")
        self.clear_btn.pack(side="right", padx=6, pady=2)
        body = tk.Frame(self)
        body.pack(fill="both", expand=True)
        self.body = body
        self.text = tk.Text(body, wrap="word", height=10, bd=0, highlightthickness=0, padx=10, pady=6,
                            font=(mono_font(), app.settings["font_size"] - 1), state="disabled", cursor="arrow")
        sb = ttk.Scrollbar(body, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        self.text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.input_row = tk.Frame(self)
        self.input_label = tk.Label(self.input_row, text="Type an answer and press Enter:", padx=10, font=(ui_font(), 9))
        self.input_label.pack(side="left")
        self.entry = ttk.Entry(self.input_row, font=(mono_font(), app.settings["font_size"] - 1))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
        self.entry.bind("<Return>", self._send)
        self.text.tag_bind("goto", "<Button-1>", self._goto_problem)
        self.text.tag_bind("goto", "<Enter>", lambda e: self.text.configure(cursor="hand2"))
        self.text.tag_bind("goto", "<Leave>", lambda e: self.text.configure(cursor="arrow"))
        self.apply_theme()

    def apply_theme(self):
        th = self.app.theme
        for w in (self, self.input_row, self.title.master):
            w.configure(bg=th["panel"])
        self.title.configure(bg=th["panel"], fg=th["panel_fg"])
        self.input_label.configure(bg=th["panel"], fg=th["info"])
        self.text.configure(bg=th["bg"], fg=th["out"], selectbackground=th["select"])
        for tag in ("out", "err", "info", "input", "ok"):
            self.text.tag_configure(tag, foreground=th[tag])
        self.text.tag_configure("hint", foreground=th["accent"])
        self.text.tag_configure("goto", underline=True)
        self.text.tag_configure("bold", font=(mono_font(), self.app.settings["font_size"] - 1, "bold"))

    def set_font_size(self, size):
        self.text.configure(font=(mono_font(), size - 1))
        self.entry.configure(font=(mono_font(), size - 1))

    def write(self, s, *tags):
        self.text.configure(state="normal")
        self.text.insert("end", s, tags or ("out",))
        self.text.configure(state="disabled")
        self.text.see("end")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def get(self):
        return self.text.get("1.0", "end-1c")

    def ask_input(self, on):
        if on:
            # packed before the output text, which would otherwise take all the room
            self.input_row.pack(fill="x", side="bottom", before=self.body)
        else:
            self.input_row.pack_forget()

    def _send(self, _e=None):
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.write(line + "\n", "input")
        self.app.send_input(line)

    def _goto_problem(self, _e=None):
        self.app.goto_problem()


class HelpPanel(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, width=320)
        self.app = app
        self.title = tk.Label(self, text="Help", font=(ui_font(), 10, "bold"), anchor="w", padx=10, pady=4)
        self.title.pack(fill="x")
        self.search_var = tk.StringVar()
        self.search = ttk.Entry(self, textvariable=self.search_var)
        self.search.pack(fill="x", padx=8, pady=(0, 6))
        self.search_var.trace_add("write", lambda *a: self.fill())
        self.placeholder = tk.Label(self, text="Search functions and statements", font=(ui_font(), 8), anchor="w", padx=10)
        self.placeholder.pack(fill="x")
        pane = tk.PanedWindow(self, orient="vertical", sashwidth=5, bd=0)
        pane.pack(fill="both", expand=True)
        lf = tk.Frame(pane)
        self.listbox = tk.Listbox(lf, activestyle="none", bd=0, highlightthickness=0, font=(mono_font(), 10), exportselection=False)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self.insert())
        df = tk.Frame(pane)
        self.detail = tk.Text(df, wrap="word", height=9, bd=0, highlightthickness=0, padx=10, pady=8, font=(ui_font(), 10),
                              state="disabled", cursor="arrow")
        self.detail.pack(fill="both", expand=True)
        row = tk.Frame(df)
        row.pack(fill="x")
        self.insert_btn = ttk.Button(row, text="Insert into code", command=self.insert, style="Small.TButton")
        self.insert_btn.pack(side="left", padx=8, pady=6)
        pane.add(lf, height=330)
        pane.add(df)
        self.frames = [self, lf, df, row]
        self.pane = pane
        self.items = []
        self.current = None
        self.fill()
        self.apply_theme()

    def apply_theme(self):
        th = self.app.theme
        for f in self.frames:
            f.configure(bg=th["panel"])
        self.pane.configure(bg=th["border"])
        self.title.configure(bg=th["panel"], fg=th["panel_fg"])
        self.placeholder.configure(bg=th["panel"], fg=th["info"])
        self.listbox.configure(bg=th["bg"], fg=th["fg"], selectbackground=th["select"], selectforeground=th["fg"])
        self.detail.configure(bg=th["bg"], fg=th["fg"])
        self.detail.tag_configure("name", font=(ui_font(), 12, "bold"), foreground=th["builtin"])
        self.detail.tag_configure("sig", font=(mono_font(), 10), foreground=th["keyword"])
        self.detail.tag_configure("group", font=(ui_font(), 8), foreground=th["info"])

    def fill(self):
        q = self.search_var.get().strip().lower()
        self.listbox.delete(0, "end")
        self.items = []
        stm = [k for k in STATEMENTS if q in k or q in STATEMENTS[k]["desc"].lower()]
        fns = [k for k in sorted(BUILTINS) if q in k or q in BUILTINS[k]["desc"].lower()]
        if stm:
            self.listbox.insert("end", "STATEMENTS AND WORDS")
            self.listbox.itemconfigure("end", fg=self.app.theme["info"])
            self.items.append(None)
            for k in stm:
                self.listbox.insert("end", "  " + k)
                self.items.append(k)
        if fns:
            self.listbox.insert("end", "BUILT-IN FUNCTIONS")
            self.listbox.itemconfigure("end", fg=self.app.theme["info"])
            self.items.append(None)
            for k in fns:
                self.listbox.insert("end", "  " + k)
                self.items.append(k)

    def _on_select(self, _e=None):
        sel = self.listbox.curselection()
        if sel and self.items[sel[0]]:
            self.show(self.items[sel[0]], select=False)

    def show(self, name, select=True):
        info = STATEMENTS.get(name) or BUILTINS.get(name)
        if not info:
            return False
        self.current = name
        group = "Statement" if name in STATEMENTS else BUILTINS[name]["group"]
        d = self.detail
        d.configure(state="normal")
        d.delete("1.0", "end")
        d.insert("end", name + "\n", "name")
        d.insert("end", group + "\n\n", "group")
        d.insert("end", info["sig"] + "\n\n", "sig")
        d.insert("end", info["desc"])
        d.configure(state="disabled")
        if select and name in self.items:
            i = self.items.index(name)
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(i)
            self.listbox.see(i)
        return True

    def insert(self):
        if not self.current:
            return
        info = STATEMENTS.get(self.current) or BUILTINS.get(self.current)
        sig = info["sig"].split("  /  ")[0]
        if self.current in BUILTINS:
            # just the name and empty brackets: the form is shown in the help
            sig = self.current + "()"
        self.app.editor.text.insert("insert", sig)
        if sig.endswith("()"):
            self.app.editor.text.mark_set("insert", "insert-1c")
        self.app.editor.text.focus_set()


class FilesPanel(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, width=190)
        self.app = app
        self.title = tk.Label(self, text="Files", font=(ui_font(), 10, "bold"), anchor="w", padx=10, pady=4)
        self.title.pack(fill="x")
        self.folder_label = tk.Label(self, text="", font=(ui_font(), 8), anchor="w", padx=10, justify="left", wraplength=170)
        self.folder_label.pack(fill="x")
        self.listbox = tk.Listbox(self, activestyle="none", bd=0, highlightthickness=0, font=(ui_font(), 10), exportselection=False)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self.listbox.bind("<Double-Button-1>", self._open)
        self.listbox.bind("<Return>", self._open)
        row = tk.Frame(self)
        row.pack(fill="x")
        ttk.Button(row, text="Choose folder", command=self.choose, style="Small.TButton").pack(side="left", padx=6, pady=6)
        self.row = row
        self.folder = None
        self.names = []
        self.apply_theme()

    def apply_theme(self):
        th = self.app.theme
        for w in (self, self.row):
            w.configure(bg=th["panel"])
        self.title.configure(bg=th["panel"], fg=th["panel_fg"])
        self.folder_label.configure(bg=th["panel"], fg=th["info"])
        self.listbox.configure(bg=th["panel"], fg=th["fg"], selectbackground=th["select"], selectforeground=th["fg"])

    def show_folder(self, folder):
        self.folder = Path(folder) if folder else None
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.names = []
        if not self.folder or not self.folder.is_dir():
            self.folder_label.configure(text="Save your program to see\nthe other files here.")
            return
        self.folder_label.configure(text=str(self.folder))
        try:
            names = sorted(p.name for p in self.folder.iterdir() if p.suffix == ".ant")
        except OSError:
            names = []
        for n in names:
            self.listbox.insert("end", "  " + n)
        self.names = names
        cur = self.app.path
        if cur and cur.parent == self.folder and cur.name in names:
            i = names.index(cur.name)
            self.listbox.selection_set(i)

    def choose(self):
        d = filedialog.askdirectory(title="Choose a folder of Antares programs", initialdir=str(self.folder or Path.home()))
        if d:
            self.show_folder(d)

    def _open(self, _e=None):
        sel = self.listbox.curselection()
        if sel:
            self.app.open_path(self.folder / self.names[sel[0]])


# ---------------------------------------------------------------------------
# The application


class App:
    def __init__(self, root, path=None, selftest=None):
        self.root = root
        self.settings = Settings()
        self.theme = THEMES[self.settings["theme"]]
        self.path = None
        self.dirty = False
        self.run = None
        self.run_started = 0
        self.problem = None
        self.stderr_buf = ""
        self.antares = runner.find_antares(self.settings["antares"])
        self.antares_version = runner.antares_version(self.antares) if self.antares else None
        self.selftest = selftest

        root.title(APP)
        root.geometry(self.settings["geometry"])
        root.minsize(820, 520)
        icon = HERE / "assets" / "icon.png"
        if icon.exists():
            try:
                self._icon = tk.PhotoImage(file=str(icon))
                root.iconphoto(True, self._icon)
            except tk.TclError:
                pass
        self._styles()
        self._menu()
        self._toolbar()
        self._layout()
        self._status()
        self._keys()
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.apply_theme()

        if path:
            self.open_path(Path(path))
        elif self.settings["last_file"] and Path(self.settings["last_file"]).is_file() and not selftest:
            self.open_path(Path(self.settings["last_file"]))
        else:
            self.editor.set(WELCOME)
            self.set_path(None)
        self.dirty = False
        self.update_title()
        self.help.show("show")
        self.editor.text.focus_set()
        if not self.antares and not selftest:
            root.after(400, self.antares_missing)
        if selftest:
            root.after(300, lambda: SelfTest(self, selftest).start())

    # ----- building the window -----

    def _styles(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        self.style = s

    def _menu(self):
        m = tk.Menu(self.root)
        f = tk.Menu(m, tearoff=False)
        f.add_command(label="New", accelerator="Ctrl+N", command=self.new)
        f.add_command(label="Open...", accelerator="Ctrl+O", command=self.open)
        self.recent_menu = tk.Menu(f, tearoff=False, postcommand=self._fill_recent)
        f.add_cascade(label="Open recent", menu=self.recent_menu)
        f.add_separator()
        f.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        f.add_command(label="Save as...", accelerator="Ctrl+Shift+S", command=self.save_as)
        f.add_separator()
        f.add_command(label="Quit", command=self.quit)
        m.add_cascade(label="File", menu=f)
        e = tk.Menu(m, tearoff=False)
        e.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self._edit("<<Undo>>"))
        e.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self._edit("<<Redo>>"))
        e.add_separator()
        e.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self._edit("<<Cut>>"))
        e.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self._edit("<<Copy>>"))
        e.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self._edit("<<Paste>>"))
        e.add_command(label="Select all", accelerator="Ctrl+A", command=self.select_all)
        e.add_separator()
        e.add_command(label="Find and replace...", accelerator="Ctrl+F", command=self.find)
        e.add_command(label="Go to line...", accelerator="Ctrl+G", command=self.goto_line)
        e.add_command(label="Comment / uncomment lines", accelerator="Ctrl+/", command=lambda: self.editor.toggle_comment())
        e.add_command(label="Complete the word", accelerator="Ctrl+Space", command=lambda: self.editor.show_completions(force=True))
        m.add_cascade(label="Edit", menu=e)
        r = tk.Menu(m, tearoff=False)
        r.add_command(label="Run", accelerator="F5", command=self.run_program)
        r.add_command(label="Stop", accelerator="Shift+F5", command=self.stop_program)
        r.add_command(label="Run in its own window", command=lambda: self.run_program(window=True))
        r.add_separator()
        r.add_command(label="Build a program file (.exe)...", accelerator="Ctrl+B", command=self.build)
        r.add_separator()
        r.add_command(label="Choose the antares program...", command=self.choose_antares)
        m.add_cascade(label="Run", menu=r)
        x = tk.Menu(m, tearoff=False)
        for path in sorted((HERE / "examples").glob("*.ant")):
            x.add_command(label=self._example_title(path), command=lambda p=path: self.open_example(p))
        m.add_cascade(label="Examples", menu=x)
        v = tk.Menu(m, tearoff=False)
        v.add_command(label="Bigger text", accelerator="Ctrl+=", command=lambda: self.zoom(1))
        v.add_command(label="Smaller text", accelerator="Ctrl+-", command=lambda: self.zoom(-1))
        v.add_separator()
        self.theme_var = tk.StringVar(value=self.settings["theme"])
        v.add_radiobutton(label="Light theme", variable=self.theme_var, value="light", command=self._theme_changed)
        v.add_radiobutton(label="Dark theme", variable=self.theme_var, value="dark", command=self._theme_changed)
        v.add_separator()
        self.show_files = tk.BooleanVar(value=True)
        self.show_help = tk.BooleanVar(value=True)
        v.add_checkbutton(label="Files panel", variable=self.show_files, command=self._panels_changed)
        v.add_checkbutton(label="Help panel", variable=self.show_help, command=self._panels_changed)
        m.add_cascade(label="View", menu=v)
        h = tk.Menu(m, tearoff=False)
        h.add_command(label="Help on the word under the cursor", accelerator="F1", command=self.help_on_word)
        h.add_command(label="Learn Antares: the beginner's book", command=lambda: webbrowser.open(BOOK_URL))
        h.add_command(label="The Antares Language Reference", command=lambda: webbrowser.open(MANUAL_URL))
        h.add_separator()
        h.add_command(label="Keyboard shortcuts", command=self.shortcuts)
        h.add_command(label=f"About {APP}", command=self.about)
        m.add_cascade(label="Help", menu=h)
        self.root.configure(menu=m)

    def _example_title(self, path):
        first = path.read_text(encoding="utf-8").splitlines()[0] if path.stat().st_size else path.stem
        return first.lstrip("# ").strip() or path.stem

    def _toolbar(self):
        bar = tk.Frame(self.root, bd=0)
        bar.pack(fill="x")
        self.toolbar = bar
        s = self.style
        s.configure("Tool.TButton", padding=(10, 5), font=(ui_font(), 10))
        s.configure("Run.TButton", padding=(14, 5), font=(ui_font(), 10, "bold"), foreground="#ffffff", background="#2e7d32")
        s.map("Run.TButton", background=[("disabled", "#9bbf9d"), ("active", "#256b29")])
        s.configure("Stop.TButton", padding=(12, 5), font=(ui_font(), 10, "bold"), foreground="#ffffff", background="#c62828")
        s.map("Stop.TButton", background=[("disabled", "#d8a5a5"), ("active", "#a52020")])
        s.configure("Small.TButton", padding=(8, 2), font=(ui_font(), 9))
        items = [("New", self.new), ("Open", self.open), ("Save", self.save)]
        for label, cmd in items:
            ttk.Button(bar, text=label, command=cmd, style="Tool.TButton").pack(side="left", padx=(6, 0), pady=6)
        self.sep1 = tk.Frame(bar, width=1)
        self.sep1.pack(side="left", fill="y", padx=10, pady=8)
        self.run_btn = ttk.Button(bar, text="▶  Run", command=self.run_program, style="Run.TButton")
        self.run_btn.pack(side="left", pady=6)
        self.stop_btn = ttk.Button(bar, text="■  Stop", command=self.stop_program, style="Stop.TButton", state="disabled")
        self.stop_btn.pack(side="left", padx=6, pady=6)
        self.sep2 = tk.Frame(bar, width=1)
        self.sep2.pack(side="left", fill="y", padx=10, pady=8)
        ttk.Button(bar, text="Help (F1)", command=self.help_on_word, style="Tool.TButton").pack(side="left", pady=6)
        self.theme_btn = ttk.Button(bar, text="Dark", command=self.toggle_theme, style="Tool.TButton")
        self.theme_btn.pack(side="right", padx=6, pady=6)
        ttk.Button(bar, text="Build .exe", command=self.build, style="Tool.TButton").pack(side="right", padx=(6, 0), pady=6)

    def _layout(self):
        self.outer = tk.PanedWindow(self.root, orient="horizontal", sashwidth=5, bd=0)
        self.outer.pack(fill="both", expand=True)
        self.files = FilesPanel(self.outer, self)
        self.middle = tk.PanedWindow(self.outer, orient="vertical", sashwidth=5, bd=0)
        self.editor = Editor(self.middle, self)
        self.output = OutputPanel(self.middle, self)
        self.middle.add(self.editor, stretch="always", minsize=160)
        self.middle.add(self.output, height=260, minsize=90)
        self.help = HelpPanel(self.outer, self)
        self.outer.add(self.files, width=190, minsize=120)
        self.outer.add(self.middle, stretch="always", minsize=360)
        self.outer.add(self.help, width=320, minsize=200)

    def _status(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", side="bottom", before=self.outer)
        self.status_bar = bar
        self.status = tk.Label(bar, text="Ready", anchor="w", padx=10, pady=3, font=(ui_font(), 9))
        self.status.pack(side="left", fill="x", expand=True)
        ver = self.antares_version or "Antares not found"
        self.ver_label = tk.Label(bar, text=ver, padx=10, font=(ui_font(), 9))
        self.ver_label.pack(side="right")
        self.pos_label = tk.Label(bar, text="Line 1, column 1", padx=10, font=(ui_font(), 9))
        self.pos_label.pack(side="right")

    def _keys(self):
        r = self.root
        r.bind("<F5>", lambda e: self.run_program())
        r.bind("<Shift-F5>", lambda e: self.stop_program())
        r.bind("<F1>", lambda e: self.help_on_word())
        r.bind("<Control-n>", lambda e: self.new())
        r.bind("<Control-o>", lambda e: self.open())
        r.bind("<Control-s>", lambda e: self.save())
        r.bind("<Control-S>", lambda e: self.save_as())
        r.bind("<Control-f>", lambda e: (self.find(), "break")[1])
        r.bind("<Control-h>", lambda e: (self.find(), "break")[1])
        r.bind("<Control-g>", lambda e: (self.goto_line(), "break")[1])
        r.bind("<Control-b>", lambda e: (self.build(), "break")[1])
        r.bind("<Control-equal>", lambda e: self.zoom(1))
        r.bind("<Control-plus>", lambda e: self.zoom(1))
        r.bind("<Control-minus>", lambda e: self.zoom(-1))
        self.editor.text.bind("<Control-a>", lambda e: (self.select_all(), "break")[1])

    # ----- looks -----

    def apply_theme(self):
        th = self.theme
        self.root.configure(bg=th["border"])
        for w in (self.toolbar, self.status_bar):
            w.configure(bg=th["panel"])
        for w in (self.sep1, self.sep2):
            w.configure(bg=th["border"])
        for w in (self.status, self.pos_label, self.ver_label):
            w.configure(bg=th["panel"], fg=th["info"])
        self.outer.configure(bg=th["border"])
        self.middle.configure(bg=th["border"])
        s = self.style
        s.configure("Tool.TButton", background=th["panel"], foreground=th["panel_fg"], bordercolor=th["border"])
        s.map("Tool.TButton", background=[("active", th["curline"])])
        s.configure("Small.TButton", background=th["panel"], foreground=th["panel_fg"], bordercolor=th["border"])
        s.map("Small.TButton", background=[("active", th["curline"])])
        s.configure("TEntry", fieldbackground=th["bg"], foreground=th["fg"], insertcolor=th["cursor"], bordercolor=th["border"])
        s.configure("Vertical.TScrollbar", background=th["panel"], troughcolor=th["bg"], bordercolor=th["border"], arrowcolor=th["info"])
        s.configure("Horizontal.TScrollbar", background=th["panel"], troughcolor=th["bg"], bordercolor=th["border"], arrowcolor=th["info"])
        self.theme_btn.configure(text="Light" if self.settings["theme"] == "dark" else "Dark")
        for p in (self.editor, self.output, self.help, self.files):
            p.apply_theme()
        self.editor.highlight_now()

    def toggle_theme(self):
        self.theme_var.set("dark" if self.settings["theme"] == "light" else "light")
        self._theme_changed()

    def _theme_changed(self):
        self.settings["theme"] = self.theme_var.get()
        self.theme = THEMES[self.settings["theme"]]
        self.apply_theme()
        self.settings.save()

    def zoom(self, d):
        size = max(8, min(28, self.settings["font_size"] + d))
        self.settings["font_size"] = size
        self.editor.set_font_size(size)
        self.output.set_font_size(size)
        self.say(f"Text size {size}")

    def _panels_changed(self):
        for panel, var, idx in ((self.files, self.show_files, 0), (self.help, self.show_help, None)):
            shown = str(panel) in [str(p) for p in self.outer.panes()]
            if var.get() and not shown:
                if idx == 0:
                    self.outer.add(panel, before=self.middle, width=190, minsize=120)
                else:
                    self.outer.add(panel, width=320, minsize=200)
            elif not var.get() and shown:
                self.outer.forget(panel)

    def say(self, msg):
        self.status.configure(text=msg)

    def update_position(self):
        line, col = self.editor.text.index("insert").split(".")
        self.pos_label.configure(text=f"Line {line}, column {int(col) + 1}")

    def update_title(self):
        name = self.path.name if self.path else "Untitled"
        self.root.title(f"{'• ' if self.dirty else ''}{name} - {APP}")

    def mark_dirty(self):
        if not self.dirty:
            self.dirty = True
            self.update_title()

    # ----- files -----

    def set_path(self, path):
        self.path = Path(path) if path else None
        if self.path:
            self.settings.add_recent(str(self.path))
            self.settings["last_file"] = str(self.path)
            self.files.show_folder(self.path.parent)
        else:
            self.files.show_folder(self.files.folder)
        self.update_title()

    def confirm_discard(self):
        if not self.dirty:
            return True
        name = self.path.name if self.path else "this program"
        a = messagebox.askyesnocancel(APP, f"Save the changes to {name} first?")
        if a is None:
            return False
        if a:
            return self.save()
        return True

    def new(self):
        if not self.confirm_discard():
            return
        self.editor.set(NEW_FILE)
        self.editor.text.mark_set("insert", "end-1c")
        self.set_path(None)
        self.dirty = False
        self.update_title()
        self.say("New program. Save it to give it a name.")

    def open(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(title="Open an Antares program", filetypes=[("Antares programs", "*.ant"), ("All files", "*.*")],
                                       initialdir=str(self.path.parent if self.path else self.files.folder or Path.home()))
        if p:
            self.open_path(Path(p), confirmed=True)

    def open_path(self, p, confirmed=False):
        if not confirmed and p != self.path and not self.confirm_discard():
            return
        try:
            code = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            messagebox.showerror(APP, f"Couldn't open {p}:\n{e}")
            return
        self.editor.set(code)
        self.set_path(p)
        self.dirty = False
        self.update_title()
        self.say(f"Opened {p.name}")

    def open_example(self, p):
        if not self.confirm_discard():
            return
        self.editor.set(p.read_text(encoding="utf-8"))
        self.set_path(None)
        self.dirty = False
        self.update_title()
        self.say(f"Example: {self._example_title(p)}. Press Run (F5) to try it; save it to keep your changes.")

    def _fill_recent(self):
        m = self.recent_menu
        m.delete(0, "end")
        recent = [p for p in self.settings["recent"] if Path(p).is_file()]
        if not recent:
            m.add_command(label="(none yet)", state="disabled")
        for p in recent:
            m.add_command(label=p, command=lambda p=p: self.open_path(Path(p)))

    def save(self):
        if not self.path:
            return self.save_as()
        try:
            self.path.write_text(self.editor.get(), encoding="utf-8", newline="")
        except OSError as e:
            messagebox.showerror(APP, f"Couldn't save {self.path}:\n{e}")
            return False
        self.dirty = False
        self.update_title()
        self.files.refresh()
        self.say(f"Saved {self.path.name}")
        self.settings.save()
        return True

    def save_as(self):
        p = filedialog.asksaveasfilename(title="Save the program", defaultextension=".ant",
                                         filetypes=[("Antares programs", "*.ant")],
                                         initialdir=str(self.path.parent if self.path else self.files.folder or Path.home()),
                                         initialfile=self.path.name if self.path else "my_program.ant")
        if not p:
            return False
        self.set_path(p)
        return self.save()

    # ----- running -----

    def run_program(self, window=False):
        if self.run and self.run.running:
            self.say("The program is still running. Press Stop to end it.")
            return
        if not self.antares:
            self.antares_missing()
            return
        code = self.editor.get()
        if self.path:
            if self.dirty and not self.save():
                return
            path, cwd = self.path, self.path.parent
        else:
            SCRATCH.mkdir(parents=True, exist_ok=True)
            path, cwd = SCRATCH / "untitled.ant", SCRATCH
            path.write_text(code, encoding="utf-8")
        self.editor.clear_problem()
        self.problem = None
        if window or runner.draws_on_screen(code):
            try:
                runner.run_in_terminal(self.antares, str(path), str(cwd))
                self.output.write(f"Running {path.name} in its own window", "info")
                self.output.write(" (it draws on the screen with key, draw or clear)\n" if not window else "\n", "info")
                self.say("Running in its own window")
            except OSError as e:
                self.output.write(f"Couldn't open a window to run it: {e}\n", "err")
            return
        self.output.clear()
        self.output.write(f"Running {path.name}\n", "info")
        self.stderr_buf = ""
        try:
            self.run = runner.Run([self.antares, str(path)], str(cwd))
        except OSError as e:
            self.output.write(f"Couldn't start Antares: {e}\n", "err")
            return
        self.run_started = time.time()
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.output.ask_input(True)
        self.say("Running... (press Stop or Shift+F5 to end it)")
        self.root.after(30, self._poll)

    def _poll(self):
        if not self.run:
            return
        done = None
        try:
            while True:
                kind, data = self.run.events.get_nowait()
                if kind == "out":
                    self.output.write(data, "out")
                elif kind == "err":
                    self.stderr_buf += data
                    self.output.write(data, "err")
                elif kind == "done":
                    done = data
        except Exception:
            pass
        if done is None:
            self.root.after(30, self._poll)
            return
        self._finished(done)

    def _finished(self, code):
        took = time.time() - self.run_started
        stopped = self.run.stopped
        self.run = None
        self.run_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.output.ask_input(False)
        if stopped:
            self.output.write("\nStopped.\n", "info")
            self.say("Stopped")
            return
        p = runner.parse_problem(self.stderr_buf)
        if p:
            line, file, msg = p
            self.problem = p
            here = self.path.name if self.path else "untitled.ant"
            same_file = file is None or file == here
            self.output.write("\n")
            if same_file:
                self.editor.mark_problem(line)
                self.output.write(f"Show me line {line}", "goto", "bold")
                self.output.write("  (it's marked in red)\n", "info")
            else:
                self.output.write(f"The problem is in {file}, line {line}.\n", "info")
            hint = hint_for(msg)
            if hint:
                self.output.write("Hint: " + hint + "\n", "hint")
            self.say(f"Problem on line {line}: {msg}")
        elif code == 0:
            self.output.write(f"\nFinished in {took:.2f} s\n", "ok")
            self.say(f"Finished in {took:.2f} s")
        else:
            self.output.write(f"\nThe program ended with code {code}.\n", "info")
            self.say(f"Ended with code {code}")

    def goto_problem(self):
        if self.problem:
            self.editor.mark_problem(self.problem[0])
            self.editor.text.focus_set()

    def stop_program(self):
        if self.run:
            self.run.stop()

    def send_input(self, line):
        if self.run:
            self.run.send(line)

    def build(self):
        if not self.antares:
            self.antares_missing()
            return
        if not self.path:
            messagebox.showinfo(APP, "Save the program first; the program file is made next to it.")
            if not self.save_as():
                return
        elif self.dirty and not self.save():
            return
        if self.run and self.run.running:
            self.say("Wait for the running program to finish first.")
            return
        self.output.clear()
        self.output.write(f"Building {self.path.name} into a program file. The first build takes a minute or two...\n"
                          "(This needs Rust, from rustup.rs.)\n", "info")
        self.stderr_buf = ""
        self.run = runner.Run([self.antares, "build", str(self.path)], str(self.path.parent))
        self.run_started = time.time()
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.say("Building...")
        self.root.after(30, self._poll)

    def choose_antares(self):
        p = filedialog.askopenfilename(title="Choose the antares program", filetypes=[("Programs", "*.exe" if os.name == "nt" else "*")])
        if p:
            v = runner.antares_version(p)
            if not v:
                messagebox.showerror(APP, "That doesn't seem to be Antares (it didn't answer 'antares version').")
                return
            self.settings["antares"] = p
            self.settings.save()
            self.antares, self.antares_version = p, v
            self.ver_label.configure(text=v)
            self.say(f"Using {v}")

    def antares_missing(self):
        win = tk.Toplevel(self.root)
        win.title("Antares isn't installed yet")
        win.transient(self.root)
        win.configure(bg=self.theme["panel"], padx=18, pady=14)
        cmd = INSTALL_WINDOWS if os.name == "nt" else INSTALL_UNIX
        where = "PowerShell" if os.name == "nt" else "the Terminal"
        tk.Label(win, text="Antares isn't installed on this computer yet.", font=(ui_font(), 11, "bold"),
                 bg=self.theme["panel"], fg=self.theme["panel_fg"]).pack(anchor="w")
        tk.Label(win, text=f"To install it, open {where}, paste this line and press Enter.\nThen start {APP} again.",
                 justify="left", bg=self.theme["panel"], fg=self.theme["panel_fg"]).pack(anchor="w", pady=(6, 6))
        e = ttk.Entry(win, width=90)
        e.insert(0, cmd)
        e.pack(fill="x")
        row = tk.Frame(win, bg=self.theme["panel"])
        row.pack(fill="x", pady=(10, 0))

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
            self.say("Install command copied")

        ttk.Button(row, text="Copy the command", command=copy).pack(side="left")
        ttk.Button(row, text="I already have it...", command=lambda: (win.destroy(), self.choose_antares())).pack(side="left", padx=6)
        ttk.Button(row, text="Close", command=win.destroy).pack(side="right")

    # ----- help -----

    def help_on_word(self):
        w = self.editor.word_at()
        if w and self.help.show(w):
            self.say(f"Help: {w}")
        else:
            self.help.search.focus_set()
            self.say("Type in the search box to find a function or statement")

    def show_help_quiet(self, name):
        self.help.show(name)

    def show_signature(self, name):
        info = BUILTINS.get(name)
        if info:
            self.say(f"{info['sig']}: {info['desc']}")
            self.help.show(name)

    def shortcuts(self):
        messagebox.showinfo("Keyboard shortcuts", "\n".join([
            "F5\tRun the program", "Shift+F5\tStop it", "F1\tHelp on the word under the cursor",
            "Ctrl+S\tSave", "Ctrl+N / Ctrl+O\tNew / Open", "Ctrl+Z / Ctrl+Y\tUndo / Redo",
            "Ctrl+F\tFind and replace", "Ctrl+G\tGo to line", "Ctrl+/\tComment or uncomment lines",
            "Ctrl+Space\tComplete the word", "Tab / Shift+Tab\tIndent / unindent", "Ctrl+= / Ctrl+-\tBigger / smaller text",
            "Ctrl+B\tBuild a program file (.exe)",
        ]))

    def about(self):
        messagebox.showinfo(f"About {APP}", f"{APP} {IDE_VERSION}\n\nA small, friendly place to write and run Antares programs.\n\n"
                            f"Using: {self.antares_version or 'Antares not found'}\nHelp written for Antares {MANUAL_VERSION}")

    # ----- editing -----

    def _edit(self, event):
        self.editor.text.event_generate(event)

    def select_all(self):
        t = self.editor.text
        t.tag_add("sel", "1.0", "end-1c")
        t.mark_set("insert", "end-1c")

    def goto_line(self):
        win = tk.Toplevel(self.root)
        win.title("Go to line")
        win.transient(self.root)
        win.resizable(False, False)
        win.configure(bg=self.theme["panel"], padx=14, pady=10)
        tk.Label(win, text="Line number:", bg=self.theme["panel"], fg=self.theme["panel_fg"]).pack(side="left")
        e = ttk.Entry(win, width=8)
        e.pack(side="left", padx=6)
        e.focus_set()

        def go(_=None):
            try:
                n = int(e.get())
            except ValueError:
                return
            t = self.editor.text
            t.mark_set("insert", f"{n}.0")
            t.see("insert")
            self.editor._update_curline()
            self.update_position()
            win.destroy()
            t.focus_set()

        e.bind("<Return>", go)
        e.bind("<Escape>", lambda _: win.destroy())
        ttk.Button(win, text="Go", command=go).pack(side="left")

    def find(self):
        FindDialog(self)

    # ----- closing -----

    def quit(self):
        if not self.confirm_discard():
            return
        if self.run:
            self.run.stop()
        self.settings["geometry"] = self.root.geometry()
        self.settings.save()
        self.root.destroy()


class FindDialog:
    def __init__(self, app):
        self.app = app
        t = app.editor.text
        th = app.theme
        win = tk.Toplevel(app.root)
        win.title("Find and replace")
        win.transient(app.root)
        win.resizable(False, False)
        win.configure(bg=th["panel"], padx=12, pady=10)
        self.win = win
        lab = dict(bg=th["panel"], fg=th["panel_fg"])
        tk.Label(win, text="Find:", **lab).grid(row=0, column=0, sticky="w")
        tk.Label(win, text="Replace with:", **lab).grid(row=1, column=0, sticky="w")
        self.find_e = ttk.Entry(win, width=32)
        self.repl_e = ttk.Entry(win, width=32)
        self.find_e.grid(row=0, column=1, padx=6, pady=3)
        self.repl_e.grid(row=1, column=1, padx=6, pady=3)
        if t.tag_ranges("sel"):
            self.find_e.insert(0, t.get("sel.first", "sel.last"))
        self.case = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text="Match capitals", variable=self.case, selectcolor=th["bg"], activebackground=th["panel"], **lab).grid(row=2, column=1, sticky="w")
        bf = tk.Frame(win, bg=th["panel"])
        bf.grid(row=0, column=2, rowspan=3, sticky="n")
        for label, cmd in (("Find next", self.next), ("Replace", self.replace), ("Replace all", self.replace_all), ("Close", self.close)):
            ttk.Button(bf, text=label, command=cmd, width=12).pack(pady=2)
        self.info = tk.Label(win, text="", **lab)
        self.info.grid(row=3, column=0, columnspan=3, sticky="w")
        self.find_e.bind("<Return>", lambda e: self.next())
        win.bind("<Escape>", lambda e: self.close())
        win.protocol("WM_DELETE_WINDOW", self.close)
        self.find_e.focus_set()

    def _search(self, start):
        t = self.app.editor.text
        q = self.find_e.get()
        if not q:
            return None
        pos = t.search(q, start, stopindex="end", nocase=not self.case.get())
        if not pos:
            pos = t.search(q, "1.0", stopindex=start, nocase=not self.case.get())
        return pos

    def next(self):
        t = self.app.editor.text
        q = self.find_e.get()
        t.tag_remove("found", "1.0", "end")
        pos = self._search("insert")
        if not pos:
            self.info.configure(text="Not found")
            return False
        end = f"{pos}+{len(q)}c"
        t.tag_remove("sel", "1.0", "end")
        t.tag_add("sel", pos, end)
        t.tag_add("found", pos, end)
        t.mark_set("insert", end)
        t.see(pos)
        self.info.configure(text="")
        return True

    def replace(self):
        t = self.app.editor.text
        q = self.find_e.get()
        if t.tag_ranges("sel"):
            sel = t.get("sel.first", "sel.last")
            if (sel == q) or (not self.case.get() and sel.lower() == q.lower()):
                t.delete("sel.first", "sel.last")
                t.insert("insert", self.repl_e.get())
        self.next()

    def replace_all(self):
        t = self.app.editor.text
        q = self.find_e.get()
        if not q:
            return
        code = t.get("1.0", "end-1c")
        flags = 0 if self.case.get() else re.IGNORECASE
        new, n = re.subn(re.escape(q), lambda m: self.repl_e.get(), code, flags=flags)
        if n:
            t.edit_separator()
            t.delete("1.0", "end")
            t.insert("1.0", new)
            t.edit_separator()
        self.info.configure(text=f"Replaced {n}")

    def close(self):
        self.app.editor.text.tag_remove("found", "1.0", "end")
        self.win.destroy()


# ---------------------------------------------------------------------------
# Self-test: drives the real window and checks what happens


class SelfTest:
    """python antares_ide.py --selftest [screenshot-folder]"""

    def __init__(self, app, shots):
        self.app = app
        self.shots = None if shots is True else Path(shots)
        self.results = []
        self.steps = [self.t_colours, self.t_complete, self.t_run_input, self.t_problem, self.t_problem_hint,
                      self.t_help, self.t_comment, self.t_indent, self.t_example, self.t_files, self.t_dark, self.t_done]

    def check(self, ok, what):
        self.results.append((ok, what))
        print(("PASS " if ok else "FAIL ") + what, flush=True)

    def start(self):
        self.app.root.attributes("-topmost", True)
        self.app.root.lift()
        self.next()

    def next(self, delay=200):
        if self.steps:
            step = self.steps.pop(0)
            self.app.root.after(delay, step)

    def wait_run(self, then, limit=200):
        if self.app.run is None or limit == 0:
            then()
        else:
            self.app.root.after(100, lambda: self.wait_run(then, limit - 1))

    def shot(self, name):
        if not self.shots:
            return
        try:
            from PIL import ImageGrab
        except ImportError:
            return
        r = self.app.root
        r.update()
        x, y, w, h = r.winfo_rootx(), r.winfo_rooty(), r.winfo_width(), r.winfo_height()
        self.shots.mkdir(parents=True, exist_ok=True)
        ImageGrab.grab((x, y, x + w, y + h)).save(self.shots / f"{name}.png")

    def t_colours(self):
        ed = self.app.editor
        ed.set('# comment\nto double(x) = x * 2\nshow "n = {len([1, 2])}", 0xFF\n')
        names = ed.text.tag_names("1.2")
        self.check("comment" in names, "comments are coloured")
        self.check("keyword" in ed.text.tag_names("2.0"), "keywords are coloured")
        self.check("define" in ed.text.tag_names("2.4"), "the name after to is coloured")
        self.check("builtin" in ed.text.tag_names("3.12"), "built-in calls inside {} in text are coloured")
        self.next()

    def t_complete(self):
        ed = self.app.editor
        ed.set("")
        ed.text.insert("insert", "upp")
        ed.show_completions()
        self.check(ed.popup is not None and "upper" in ed._popup_items, "typing 'upp' offers upper")
        ed.accept_completion()
        self.check(ed.get() == "upper()", "accepting a function adds its brackets")
        self.next()

    def t_run_input(self):
        ed = self.app.editor
        ed.set('name = input("Your name? ")\nshow "Hello, {name}!"\nshow len(name)\n')
        self.app.run_program()
        self.check(self.app.run is not None, "Run starts the program")

        def answer():
            row = self.app.output.input_row
            self.app.root.update()
            self.check(row.winfo_ismapped() and row.winfo_height() > 10, "the answer box is visible while the program waits")
            self.app.output.entry.insert(0, "Maya")
            self.app.output._send()
            self.wait_run(after)

        def after():
            out = self.app.output.get()
            self.check("Your name? Maya" in out and "Hello, Maya!" in out and "\n4\n" in out, "input() gets the typed answer")
            self.check("Finished in" in out, "a finished run says so")
            self.shot("run_input")
            self.next()

        self.app.root.after(800, answer)

    def t_problem(self):
        ed = self.app.editor
        ed.set('total = 5\nshow total\nshow totl\n')
        self.app.run_program()

        def after():
            self.check(ed.problem_line == 3, "a problem marks its line (3)")
            self.check("problem" in ed.text.tag_names("3.2"), "the problem line is shown in red")
            self.check("Did you mean 'total'" in self.app.output.get(), "the problem message is shown")
            self.check("Hint:" in self.app.output.get(), "a hint is given")
            self.shot("problem")
            ed.text.insert("end", " ")
            self.app.root.update()
            self.check(ed.problem_line is None, "editing clears the mark")
            self.next()

        self.wait_run(after)

    def t_problem_hint(self):
        ed = self.app.editor
        ed.set('x = 3\nwhen x = 3 { show 1 }\n')
        self.app.run_program()

        def after():
            out = self.app.output.get()
            self.check(ed.problem_line == 2 and "two equals signs" in out, "= instead of == gets its own hint")
            self.next()

        self.wait_run(after)

    def t_help(self):
        ed = self.app.editor
        ed.set("show sort_by(xs, f)\n")
        ed.text.mark_set("insert", "1.8")
        self.app.help_on_word()
        self.check(self.app.help.current == "sort_by", "F1 shows help for the word under the cursor")
        self.app.help.search_var.set("date")
        self.check("now" in self.app.help.items, "searching 'date' finds now")
        self.app.help.search_var.set("")
        self.next()

    def t_comment(self):
        ed = self.app.editor
        ed.set("show 1\n    show 2\n")
        ed.text.tag_add("sel", "1.0", "2.end")
        ed.toggle_comment()
        self.check(ed.get() == "# show 1\n    # show 2\n", "Ctrl+/ comments lines out")
        ed.text.tag_add("sel", "1.0", "2.end")
        ed.toggle_comment()
        self.check(ed.get() == "show 1\n    show 2\n", "and back in")
        self.next()

    def t_indent(self):
        ed = self.app.editor
        ed.set("")
        ed.text.insert("insert", "repeat 3 {}")
        ed.text.mark_set("insert", "1.10")
        ed._on_return(None)
        self.check(ed.get() == "repeat 3 {\n    \n}", "Enter after { indents and puts } below")
        self.next()

    def t_example(self):
        examples = sorted((HERE / "examples").glob("*.ant"))
        self.check(len(examples) >= 10, f"the examples are there ({len(examples)})")
        self.app.dirty = False  # otherwise it asks whether to save the test's code first
        self.app.open_example(examples[0])
        self.app.run_program()

        def after():
            self.check("Hello, world!" in self.app.output.get(), "an example opens and runs")
            self.next()

        self.wait_run(after)

    def t_files(self):
        d = Path(tempfile.mkdtemp(prefix="antares_ide_test_"))
        (d / "other.ant").write_text("show 2\n", encoding="utf-8")
        self.app.editor.set("show 1\n")
        self.app.set_path(d / "mine.ant")
        self.app.save()
        self.check(self.app.files.names == ["mine.ant", "other.ant"], "the files panel lists the folder's programs")
        self.check((d / "mine.ant").read_text(encoding="utf-8") == "show 1\n" and not self.app.dirty, "Save writes the file")
        self.app.open_path(d / "other.ant")
        self.check(self.app.editor.get() == "show 2\n" and self.app.path.name == "other.ant", "opening a file shows it")
        self.next()

    def t_dark(self):
        # a saved program in a folder of programs, run: what the screenshots show
        d = Path(tempfile.mkdtemp(prefix="antares_ide_shots_")) / "my programs"
        d.mkdir()
        for name, src in (("grade_book.ant", "04_grade_book.ant"), ("times_table.ant", "02_times_table.ant"), ("hello.ant", "01_hello.ant")):
            (d / name).write_text((HERE / "examples" / src).read_text(encoding="utf-8"), encoding="utf-8")
        self.app.open_path(d / "grade_book.ant")
        self.app.editor.text.mark_set("insert", "12.8")
        self.app.help_on_word()
        self.app.run_program()

        def after():
            out = self.app.output.get()
            self.check("Cleo" in out and "91.7" in out, "a saved program runs from its folder")
            light = self.app.settings["theme"] == "light"
            self.shot("light" if light else "dark")
            self.app.toggle_theme()
            self.shot("dark" if light else "light")
            self.app.toggle_theme()
            self.check(True, "themes switch")
            self.next()

        self.wait_run(after)

    def t_done(self):
        failed = [w for ok, w in self.results if not ok]
        print(f"{len(self.results) - len(failed)} of {len(self.results)} checks passed", flush=True)
        self.app.dirty = False
        self.app.root.after(100, lambda: (self.app.root.destroy(), os._exit(1 if failed else 0)))


def main():
    args = sys.argv[1:]
    selftest = None
    if args and args[0] == "--selftest":
        selftest = args[1] if len(args) > 1 else True
        args = []
        # don't touch the real settings
        global SETTINGS_FILE
        SETTINGS_FILE = Path(tempfile.gettempdir()) / "antares_ide_selftest.json"
        SETTINGS_FILE.unlink(missing_ok=True)
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # sharp text on high-resolution screens
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    App(root, args[0] if args else None, selftest=selftest)
    root.mainloop()


if __name__ == "__main__":
    main()
