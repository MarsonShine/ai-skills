"""Regression checks for required harness documents and non-destructive sync."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[1] / "skills/bootstrap-harness/scripts/harness.py"
SUPPORT_FILES = (
    "docs/tasks/active.md",
    "docs/status.md",
    "docs/harness.md",
    ".github/pull_request_template.md",
)


class SupportDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harness-documents-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        result = self.run_engine("init", "--write")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_engine(self, command, *args):
        return subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(ENGINE), command,
             "--root", str(self.root), *args],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def test_initialized_project_passes(self):
        result = self.run_engine("check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_rejects_each_missing_or_empty_document(self):
        for relative in SUPPORT_FILES:
            path = self.root / relative
            original = path.read_bytes()
            for state in ("missing", "empty"):
                with self.subTest(document=relative, state=state):
                    if state == "missing":
                        path.unlink()
                    else:
                        path.write_text(" \n", encoding="utf-8")
                    result = self.run_engine("check")
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn(relative, result.stdout.replace("\\", "/"))
                    self.assertIn(state, result.stdout)
                path.write_bytes(original)

    def test_sync_restores_documents_without_overwriting_project_content(self):
        for index, relative in enumerate(SUPPORT_FILES):
            path = self.root / relative
            if index % 2:
                path.write_text("\n", encoding="utf-8")
            else:
                path.unlink()
        result = self.run_engine("sync", "--write")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative in SUPPORT_FILES:
            self.assertTrue((self.root / relative).read_text(encoding="utf-8").strip())
        self.assertEqual(self.run_engine("check").returncode, 0)

        expected = {}
        for relative in SUPPORT_FILES:
            content = (f"# Project-owned {relative}\r\n\r\n"
                       "Keep task results, acceptance criteria and local commands.\r\n")
            expected[relative] = content.encode("utf-8")
            (self.root / relative).write_bytes(expected[relative])
        result = self.run_engine("sync", "--write")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative, content in expected.items():
            self.assertEqual((self.root / relative).read_bytes(), content)

    def test_sync_dry_run_preserves_missing_and_existing_documents(self):
        missing = self.root / SUPPORT_FILES[0]
        missing.unlink()
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        result = self.run_engine("sync")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = {p.relative_to(self.root): p.read_bytes()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
