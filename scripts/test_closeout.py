"""Exercise session closeout through its public CLI using isolated Git fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENGINE = Path(__file__).resolve().parents[1] / "skills/bootstrap-harness/scripts/harness.py"


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="closeout-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("PROGRESS.md", "Status: idle\nTask: none\nNext: Select the next requested task.\n")
        self.write("active.md", "Status: idle\nTask: none\nNext: Wait for the next task.\n")
        self.write(".gitignore", ".scratch/\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"})

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_check(self, *extra):
        result = subprocess.run([sys.executable, "-B", str(ENGINE), "closeout", "--root", str(self.root),
                                 "--state", "PROGRESS.md", "--task", "active.md", *extra],
                                capture_output=True, text=True, check=False)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, int(bool(report["errors"])))
        return report

    def codes(self, report):
        return {item["code"] for item in report["errors"]}

    def snapshot(self):
        return {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_read_only_repeatable_complete_check(self):
        before = self.snapshot()
        first = self.run_check("--complete")
        self.assertEqual(first["result"], "passed")
        self.assertEqual(first, self.run_check("--complete"))
        self.assertEqual(before, self.snapshot())

    def test_conflict_and_completed_contract_are_rejected(self):
        self.write("active.md", "Status: completed\nTask: T-OLD\nNext: Archive the result.\n")
        codes = self.codes(self.run_check("--scope", "active.md"))
        self.assertTrue({"state_conflict", "invalid_status"} <= codes)

    def test_unfinished_handoff_is_valid_but_not_complete(self):
        for name in ("active.md", "PROGRESS.md"):
            self.write(name, "Status: blocked\nTask: T-1\nBlocker: dependency unavailable\nNext: Restore dependency.\n")
        args = ("--scope", "active.md", "--scope", "PROGRESS.md")
        self.assertEqual(self.run_check(*args)["result"], "passed")
        self.assertIn("unfinished_task", self.codes(self.run_check(*args, "--complete")))

    def test_missing_fields_and_local_links(self):
        self.write("PROGRESS.md", "Status: idle\nTask: none\nNext: \nNot a next action\n")
        self.assertIn("invalid_field", self.codes(self.run_check("--scope", "PROGRESS.md")))
        self.write("PROGRESS.md", "Status: idle\nTask: none\n[missing](missing.md)\n")
        codes = self.codes(self.run_check("--scope", "PROGRESS.md"))
        self.assertTrue({"invalid_field", "broken_link"} <= codes)
        self.write("PROGRESS.md", "Status: idle\nTask: none\nNext: Read [notes](<notes with spaces.md>).\n")
        self.write("notes with spaces.md", "notes")
        self.assertEqual(self.run_check("--scope", "PROGRESS.md", "--scope", "notes with spaces.md")["result"], "passed")

    def test_untracked_staged_and_committed_changes_need_scope(self):
        self.write("other.txt", "user-owned work")
        self.assertIn("unexplained_change", self.codes(self.run_check()))
        self.assertEqual(self.run_check("--preserve", "other.txt=pre-existing user work")["result"], "passed")
        base = self.git("rev-parse", "HEAD").stdout.decode().strip()
        self.git("add", "other.txt")
        self.assertIn("unexplained_change", self.codes(self.run_check()))
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "extra")
        self.assertIn("unexplained_change", self.codes(self.run_check("--base", base)))
        self.assertEqual(self.run_check("--base", base, "--scope", "other.txt")["result"], "passed")

    def test_ignored_scratch_is_explicit_and_never_deleted(self):
        self.write(".scratch/owned.txt", "temporary")
        self.assertEqual(self.run_check()["result"], "passed")
        args = ("--scratch", ".scratch/owned.txt")
        self.assertIn("scratch_remaining", self.codes(self.run_check(*args)))
        self.assertEqual(self.run_check(*args, "--preserve", ".scratch/owned.txt=needed for diagnosis")["result"], "passed")
        self.assertTrue((self.root / ".scratch/owned.txt").exists())
        self.assertIn("inspection_error", self.codes(self.run_check("--scratch", "../outside")))
        self.assertIn("inspection_error", self.codes(self.run_check("--scope", ".")))


if __name__ == "__main__":
    unittest.main()
