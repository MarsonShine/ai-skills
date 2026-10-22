"""Read-only checks for explicit session state, scope and scratch paths."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def inspect_closeout(root, state, task=None, scopes=(), preserved=(), scratch=(), base=None, complete=False):
    root = Path(root).resolve()
    report = {"errors": [], "warnings": [], "inspected_files": [],
              "changed_files": [], "scratch_files": [], "preserved": {}}

    def error(code, path, detail):
        report["errors"].append({"code": code, "path": str(path), "detail": detail})

    def relative(value):
        path = Path(value)
        if path.is_absolute() or not value.strip():
            raise ValueError("use a non-empty repository-relative path")
        resolved = (root / path).resolve()
        resolved.relative_to(root)
        return resolved.relative_to(root).as_posix()

    def git(*args):
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            capture_output=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}, check=False,
        )
        if result.returncode:
            raise ValueError("Git inspection failed; verify repository access and the supplied base")
        return result.stdout

    def names(*args):
        return {name.decode("utf-8", errors="surrogateescape")
                for name in git(*args).split(b"\0") if name}

    def within(path, prefix):
        return path == prefix or path.startswith(prefix + "/")

    def document(value):
        name = relative(value)
        path = root / name
        if not path.is_file():
            error("missing_document", name, "current-state document is missing")
            return {}
        text = path.read_text(encoding="utf-8-sig")
        report["inspected_files"].append(name)
        # Code examples are not declarations or navigational links.
        visible = []
        fence = None
        for line in text.splitlines():
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if marker:
                if fence is None:
                    fence = marker[1][0]
                elif fence == marker[1][0]:
                    fence = None
                continue
            if fence is None:
                visible.append(line)
        body = "\n".join(visible)
        fields = {}
        for key in ("Status", "Task", "Next"):
            values = re.findall(r"^" + key + r":[ \t]*(.*)$", body, re.MULTILINE)
            if len(values) != 1 or not values[0].strip():
                error("invalid_field", name, f"exactly one non-empty {key} field is required")
            else:
                fields[key] = values[0].strip()
        status = fields.get("Status")
        if status not in {"idle", "in_progress", "blocked"}:
            error("invalid_status", name, "use idle, in_progress or blocked; archive completed contracts")
        if status == "idle" and fields.get("Task") != "none":
            error("idle_task", name, "idle requires Task: none")
        if status in {"in_progress", "blocked"} and fields.get("Task") == "none":
            error("missing_task", name, "unfinished work requires its task identifier")
        if status == "blocked" and not re.search(r"^Blocker:[ \t]*\S", body, re.MULTILINE):
            error("missing_blocker", name, "blocked work requires a Blocker field")
        if complete and status != "idle":
            error("unfinished_task", name, "--complete requires an idle current entry after archival")
        if len(text.splitlines()) > 80:
            report["warnings"].append({"code": "long_entry", "path": name,
                                       "detail": "review for consolidation; do not truncate constraints"})
        pattern = r'\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+["\'][^"\']*["\'])?\s*\)'
        for match in re.finditer(pattern, body):
            target = match[1] or match[2]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            link = unquote(parsed.path)
            candidate = (root / link.lstrip("/")) if link.startswith("/") else (path.parent / link)
            try:
                candidate.resolve().relative_to(root)
            except ValueError:
                error("outside_link", name, "local link leaves repository: " + target)
                continue
            if not candidate.exists():
                error("broken_link", name, target)
        return fields

    try:
        allowed = []
        for value in scopes:
            name = relative(value)
            if name == ".":
                raise ValueError("scope must name a file or directory below the repository root")
            allowed.append(name)
        for item in preserved:
            name, separator, reason = item.partition("=")
            if not separator or not reason.strip():
                raise ValueError("--preserve requires PATH=reason")
            name = relative(name)
            if name == ".":
                raise ValueError("preservation must name a file or directory below the root")
            report["preserved"][name] = reason.strip()
        current = document(state)
        if task:
            active = document(task)
            for key in ("Status", "Task"):
                if key in current and key in active and current[key] != active[key]:
                    error("state_conflict", task, key + " disagrees with the current-state entry")
        changed = names("diff", "--name-only", "--no-renames", "-z", "HEAD", "--")
        changed |= names("ls-files", "--others", "--exclude-standard", "-z")
        if base:
            revision = git("rev-parse", "--verify", "--end-of-options", base + "^{commit}").strip().decode("ascii")
            changed |= names("diff", "--name-only", "--no-renames", "-z", revision, "HEAD", "--")
            report["base"] = revision
        report["changed_files"] = sorted(changed)
        for name in sorted(changed):
            if not any(within(name, prefix) for prefix in allowed + list(report["preserved"])):
                error("unexplained_change", name, "declare the slice scope or a preservation reason")
        for value in scratch:
            name = relative(value)
            if name == ".":
                raise ValueError("scratch inspection must name a task-owned path below the root")
            path = root / name
            if path.exists():
                report["scratch_files"].append(name)
                if not any(within(name, prefix) for prefix in report["preserved"]):
                    error("scratch_remaining", name, "inspect for disposal or document why it must be retained")
    except (OSError, ValueError, UnicodeError) as exc:
        error("inspection_error", "", str(exc))
    report["result"] = "failed" if report["errors"] else "passed"
    return report
