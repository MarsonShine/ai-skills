"""Exercise concurrent task handoff through the CLI in real linked Git worktrees."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ENGINE = Path(__file__).resolve().parents[1] / "skills/bootstrap-harness/scripts/harness.py"


class WorktreeTaskTests(unittest.TestCase):
    def setUp(self):
        contents = tempfile.TemporaryDirectory(prefix="parallel-harness-")
        self.addCleanup(contents.cleanup)
        self.base = Path(contents.name).resolve()
        self.repo = self.base / "integration"
        self.a = self.base / "module A"
        self.b = self.base / "module B"
        self.repo.mkdir()
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        self.git("init", "-q")
        self.write(self.repo, ".gitignore", "/HANDOFF.md\n")
        state = "Status: idle\nTask: none\nNext: Select an accepted task.\n"
        self.write(self.repo, "docs/status.md", state)
        self.write(self.repo, "docs/tasks/active.md", state)
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "integration snapshot")
        self.git("worktree", "add", "-q", "-b", "module-a", str(self.a))
        self.git("worktree", "add", "-q", "-b", "module-b", str(self.b))

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], env=self.env, check=True, capture_output=True)

    @staticmethod
    def write(root, name, content):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def card(self, root, task, *, status="in_progress", next_action="Run module checks.", extra=""):
        self.write(root, "HANDOFF.md",
                   f"# Module handoff\n\nStatus: {status}\nTask: {task}\nNext: {next_action}\n{extra}")

    def invoke(self, command, root, *args, ok=True):
        result = subprocess.run([sys.executable, "-B", str(ENGINE), command, "--root", str(root), *args],
                                env=self.env, text=True, encoding="utf-8", capture_output=True, check=False)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(bool(report["errors"]), not ok, report)
        return report

    def test_close_a_and_resume_b_without_touching_shared_state(self):
        self.card(self.a, "T-A")
        self.card(self.b, "T-B", next_action="Check the Excel import report.")
        self.write(self.a, "module-a/notes.txt", "A work\n")
        self.write(self.b, "module-b/notes.txt", "B work\n")
        initial = self.invoke("tasks", self.repo)
        self.assertCountEqual([(t["task"], t["status"]) for t in initial["tasks"]],
                              [("T-A", "in_progress"), ("T-B", "in_progress")])
        self.invoke("closeout", self.a, "--worktree-task", "--scope", "HANDOFF.md", "--scope", "module-a")

        self.write(self.a, "docs/validation/T-A/checks.md", "# Module A passed\n")
        self.card(self.a, "T-A", status="completed", next_action="Integrate module A.",
                  extra="Evidence: [verification](docs/validation/T-A/checks.md)\n")
        # Snapshot both checkouts, the integration state and Git's indexes/administrative files.
        def snapshot():
            return {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}

        before = snapshot()
        result = self.invoke("closeout", self.a, "--worktree-task", "--complete",
                             "--scope", "HANDOFF.md", "--scope", "module-a", "--scope", "docs/validation/T-A")
        self.assertNotIn("module-b/notes.txt", result["changed_files"])
        self.invoke("closeout", self.b, "--worktree-task", "--scope", "module-b", "--complete", ok=False)

        # A fresh process launched from B must resolve B's next action after A closes.
        resumed = self.invoke("tasks", self.b)["tasks"]
        self.assertCountEqual([(t["task"], t["status"]) for t in resumed],
                              [("T-A", "completed"), ("T-B", "in_progress")])
        work_b = next(t for t in resumed if t["task"] == "T-B")
        self.assertEqual(Path(work_b["worktree"]).resolve(), self.b)
        self.assertEqual(work_b["next"], "Check the Excel import report.")
        self.invoke("closeout", self.b, "--worktree-task", "--scope", "module-b")
        self.invoke("closeout", self.repo, "--task", "docs/tasks/active.md", "--complete")
        self.assertEqual(before, snapshot())

    def test_duplicate_id_across_blocked_and_running_worktrees(self):
        self.card(self.a, "T-A")
        self.card(self.b, "T-A", status="blocked", extra="Blocker: waiting for test data.\n")
        self.invoke("tasks", self.repo, ok=False)
        self.card(self.b, "T-B", status="blocked", extra="Blocker: waiting for test data.\n")
        self.assertCountEqual([(t["task"], t["status"]) for t in self.invoke("tasks", self.a)["tasks"]],
                              [("T-A", "in_progress"), ("T-B", "blocked")])

    def test_scoping_a_force_added_handoff_does_not_make_it_local(self):
        self.card(self.a, "T-A")
        subprocess.run(["git", "-C", str(self.a), "add", "--force", "--", "HANDOFF.md"],
                       env=self.env, check=True, capture_output=True)
        report = self.invoke("closeout", self.a, "--worktree-task", "--scope", "HANDOFF.md", ok=False)
        self.assertIn("tracked_handoff", [item["code"] for item in report["errors"]])

    def test_completed_handoff_requires_existing_evidence_in_its_worktree(self):
        self.card(self.a, "T-A", status="completed")
        self.invoke("closeout", self.a, "--worktree-task", "--complete", ok=False)
        self.card(self.a, "T-A", status="completed", extra="Evidence: passed on my machine.\n")
        self.invoke("closeout", self.a, "--worktree-task", "--complete", ok=False)
        self.write(self.b, "module-a/checks.md", "Exists only in B\n")
        self.card(self.a, "T-A", status="completed", extra="Evidence: [checks](module-a/checks.md)\n")
        self.invoke("closeout", self.a, "--worktree-task", "--complete", ok=False)
        self.write(self.a, "module-a/checks.md", "Passed in A\n")
        self.invoke("closeout", self.a, "--worktree-task", "--complete", "--scope", "module-a")


if __name__ == "__main__":
    unittest.main()
