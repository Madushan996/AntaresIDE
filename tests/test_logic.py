"""Tests for the parts of the IDE that don't need the window.

  python -m unittest discover tests
"""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import highlight  # noqa: E402
import runner  # noqa: E402


def kinds(code):
    return [(code[s:e], k) for s, e, k in highlight.tokens(code)]


class Colouring(unittest.TestCase):
    def test_basic_parts(self):
        got = kinds('# note\nto f(x) = x + 1\nshow "hi", 0xFF, 2.5e3, yes\n')
        self.assertIn(("# note", "comment"), got)
        self.assertIn(("to", "keyword"), got)
        self.assertIn(("f", "define"), got)
        self.assertIn(('"hi"', "text"), got)
        self.assertIn(("0xFF", "number"), got)
        self.assertIn(("2.5e3", "number"), got)
        self.assertIn(("yes", "constant"), got)

    def test_code_inside_text(self):
        got = kinds('show "n = {len(xs)} and {upper("a")}"')
        self.assertIn(("len", "builtin"), got)
        self.assertIn(("upper", "builtin"), got)
        self.assertIn(('"a"', "text"), got)
        self.assertEqual(sum(1 for _, k in got if k == "interp"), 4)

    def test_builtin_only_when_called(self):
        got = kinds("len = 3\nshow len(xs)\nxs -> sort\n")
        self.assertEqual([t for t in got if t[0] == "len"], [("len", "builtin")])
        self.assertIn(("sort", "builtin"), got)

    def test_hash_inside_text_is_not_a_comment(self):
        got = kinds('show "#1 fan" # real\n')
        self.assertIn(('"#1 fan"', "text"), got)
        self.assertIn(("# real", "comment"), got)

    def test_unfinished_code_does_not_fail(self):
        for code in ['show "open', 'show "{len(', "to", '"\\', "{{{", "0x", "# "]:
            highlight.tokens(code)

    def test_index_conversion(self):
        index = highlight.offsets_to_index("ab\ncd\n")
        self.assertEqual(index(0), "1.0")
        self.assertEqual(index(4), "2.1")


class Problems(unittest.TestCase):
    def test_parse(self):
        msg = "\nProblem on line 2: I don't know what 'totl' is. Did you mean 'total'?\n     2 | show totl\n"
        self.assertEqual(runner.parse_problem(msg), (2, None, "I don't know what 'totl' is. Did you mean 'total'?"))

    def test_parse_other_file(self):
        self.assertEqual(runner.parse_problem("Problem on line 7 of shapes.ant: oops"), (7, "shapes.ant", "oops"))

    def test_no_problem(self):
        self.assertIsNone(runner.parse_problem("all good\n"))

    def test_draws_on_screen(self):
        self.assertTrue(runner.draws_on_screen("x = key()\n"))
        self.assertTrue(runner.draws_on_screen("draw(picture)"))
        self.assertFalse(runner.draws_on_screen("# key() in a comment\nshow 1"))
        self.assertFalse(runner.draws_on_screen("monkey = 3"))


@unittest.skipUnless(runner.find_antares(), "antares isn't installed")
class Running(unittest.TestCase):
    def collect(self, run, answers=()):
        out, err, code = "", "", None
        answers = list(answers)
        start = time.time()
        while code is None and time.time() - start < 30:
            try:
                kind, data = run.events.get(timeout=0.2)
            except Exception:
                continue
            if kind == "out":
                out += data
                if answers and data.endswith("? "):
                    run.send(answers.pop(0))
            elif kind == "err":
                err += data
            else:
                code = data
        return out, err, code

    def test_output_and_input(self, tmp=None):
        import tempfile
        d = Path(tempfile.mkdtemp())
        p = d / "t.ant"
        p.write_text('n = input("Name? ")\nshow "Hi {n}"\n', encoding="utf-8")
        run = runner.Run([runner.find_antares(), str(p)], str(d))
        out, err, code = self.collect(run, ["Ada"])
        self.assertEqual(code, 0)
        self.assertIn("Name? ", out)
        self.assertIn("Hi Ada", out)

    def test_problem_reported(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        p = d / "t.ant"
        p.write_text("show 1\nshow nope\n", encoding="utf-8")
        run = runner.Run([runner.find_antares(), str(p)], str(d))
        out, err, code = self.collect(run)
        self.assertNotEqual(code, 0)
        self.assertEqual(runner.parse_problem(err)[0], 2)

    def test_stop(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        p = d / "t.ant"
        p.write_text("while yes { x = 1 }\n", encoding="utf-8")
        run = runner.Run([runner.find_antares(), str(p)], str(d))
        time.sleep(0.5)
        run.stop()
        out, err, code = self.collect(run)
        self.assertTrue(run.stopped)
        self.assertIsNotNone(code)


class Examples(unittest.TestCase):
    def test_every_example_has_a_title(self):
        for p in (Path(__file__).resolve().parent.parent / "examples").glob("*.ant"):
            first = p.read_text(encoding="utf-8").splitlines()[0]
            self.assertTrue(first.startswith("# ") and len(first) > 3, p.name)

    @unittest.skipUnless(runner.find_antares(), "antares isn't installed")
    def test_examples_run(self):
        import subprocess
        for p in sorted((Path(__file__).resolve().parent.parent / "examples").glob("*.ant")):
            code = p.read_text(encoding="utf-8")
            if runner.draws_on_screen(code) or "input(" in code:
                continue
            r = subprocess.run([runner.find_antares(), str(p)], capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, f"{p.name}: {r.stderr}")


if __name__ == "__main__":
    unittest.main()
