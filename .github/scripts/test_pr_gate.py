import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pr_gate

TOKEN = "ghp_" + "A" * 36


class AddedLinesTests(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        self.run_git("init", "-q")
        self.run_git("config", "core.autocrlf", "false")
        self.run_git("commit", "-q", "--allow-empty", "-m", "base")

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def run_git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True)

    def commit(self, name, text):
        with open(name, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        self.run_git("add", name)
        self.run_git("commit", "-q", "-m", "change")

    def test_lines_starting_with_two_plus_signs_are_checked(self):
        self.commit("notes.md", "a\n++ " + TOKEN + "\nb\n")
        lines = list(pr_gate.added_lines("HEAD^1", "HEAD", "notes.md"))
        self.assertEqual(lines, [(1, "a"), (2, "++ " + TOKEN), (3, "b")])
        errors = pr_gate.check_lines("HEAD^1", "HEAD", ["notes.md"])
        self.assertEqual(errors, [("notes.md:2", "access token")])

    def test_file_headers_are_not_added_lines(self):
        self.commit("a.rs", "fn a() {}\n")
        self.assertEqual(list(pr_gate.added_lines("HEAD^1", "HEAD", "a.rs")), [(1, "fn a() {}")])

    def test_line_numbers_follow_each_hunk(self):
        self.commit("b.md", "".join("%d\n" % i for i in range(1, 11)))
        self.commit("b.md", "".join(("+++x\n" if i in (3, 8) else "%d\n" % i) for i in range(1, 11)))
        self.assertEqual(list(pr_gate.added_lines("HEAD^1", "HEAD", "b.md")), [(3, "+++x"), (8, "+++x")])


if __name__ == "__main__":
    unittest.main()
