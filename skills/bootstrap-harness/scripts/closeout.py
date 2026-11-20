"""Read-only checks for explicit session state, scope and scratch paths."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def git_output(root, *args):
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        capture_output=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}, check=False,
    )
    if result.returncode:
        raise ValueError("Git inspection failed; verify repository access and the supplied base")
    return result.stdout


def inspect_document(root, name, report, *, complete=False, worktree_task=False):
    def error(code, path, detail):
        report["errors"].append({"code": code, "path": str(path), "detail": detail})

    path = root / name
    if worktree_task and path.is_symlink():
        error("linked_handoff", name, "the handoff must belong to this working tree")
        return {}
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
    finished = "completed" if worktree_task else "idle"
    if status not in {finished, "in_progress", "blocked"}:
        error("invalid_status", name, f"use {finished}, in_progress or blocked")
    if status == "idle" and fields.get("Task") != "none":
        error("idle_task", name, "idle requires Task: none")
    if status in {"in_progress", "blocked", "completed"} and fields.get("Task") == "none":
        error("missing_task", name, "a task identifier is required")
    if status == "blocked" or (worktree_task and status == "completed"):
        key = "Blocker" if status == "blocked" else "Evidence"
        values = re.findall(r"^" + key + r":[ \t]*(.*)$", body, re.MULTILINE)
        if len(values) != 1 or not values[0].strip():
            error("missing_" + key.lower(), name, f"{status} work requires one non-empty {key} field")
        else:
            fields[key] = values[0].strip()
    if complete and status != finished:
        error("unfinished_task", name, f"--complete requires {finished} status")
    if len(text.splitlines()) > 80:
        report["warnings"].append({"code": "long_entry", "path": name,
                                   "detail": "review for consolidation; do not truncate constraints"})
    pattern = r'\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+["\'][^"\']*["\'])?\s*\)'
    evidence_targets = set()
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
        elif ("Evidence" in fields and not link.startswith("/") and not Path(link).is_absolute()
              and candidate.is_file() and candidate.resolve() != path.resolve()):
            evidence_targets.add(target)
    if "Evidence" in fields and not any(
        (match[1] or match[2]) in evidence_targets for match in re.finditer(pattern, fields["Evidence"])
    ):
        error("invalid_evidence", name, "Evidence must link to a local result file in this worktree")
    return fields


def inspect_closeout(root, state, task=None, scopes=(), preserved=(), scratch=(), base=None, complete=False,
                     *, worktree_task=False):
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

    def names(*args):
        return {name.decode("utf-8", errors="surrogateescape")
                for name in git_output(root, *args).split(b"\0") if name}

    def within(path, prefix):
        return path == prefix or path.startswith(prefix + "/")

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
        if worktree_task:
            toplevel = os.fsdecode(git_output(root, "rev-parse", "--show-toplevel")).rstrip("\r\n")
            if Path(toplevel).resolve() != root:
                raise ValueError("--root must be the root of the task's Git worktree")
            if git_output(root, "ls-files", "-z", "--", "HANDOFF.md"):
                error("tracked_handoff", "HANDOFF.md", "keep the worktree-local card out of Git's index")
            allowed.append("HANDOFF.md")
        current = inspect_document(root, "HANDOFF.md" if worktree_task else relative(state),
                                   report, complete=complete, worktree_task=worktree_task)
        if worktree_task:
            report["worktree"] = str(root)
            report.update({key.lower(): value for key, value in current.items()})
        if task:
            active = inspect_document(root, relative(task), report, complete=complete)
            for key in ("Status", "Task"):
                if key in current and key in active and current[key] != active[key]:
                    error("state_conflict", task, key + " disagrees with the current-state entry")
        changed = names("diff", "--name-only", "--no-renames", "-z", "HEAD", "--")
        changed |= names("ls-files", "--others", "--exclude-standard", "-z")
        if base:
            revision = git_output(root, "rev-parse", "--verify", "--end-of-options", base + "^{commit}").strip().decode("ascii")
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


def list_worktree_tasks(root):
    """Read cards from this repository's registered worktrees using Git's NUL format."""
    report = {"tasks": [], "errors": [], "warnings": []}
    active_ids = {}
    try:
        records = git_output(root, "worktree", "list", "--porcelain", "-z")
    except (ValueError, OSError) as exc:
        report["errors"].append({"code": "inspection_error", "detail": str(exc)})
        records = b""
    for record in records.split(b"\0\0"):
        if not record:
            continue
        data = {}
        for field in record.split(b"\0"):
            key, _, value = field.partition(b" ")
            data[key] = os.fsdecode(value)
        if b"bare" in data:
            continue
        tree = Path(data[b"worktree"])
        if b"prunable" in data or not tree.is_dir():
            report["warnings"].append({"code": "unavailable_worktree", "worktree": str(tree)})
            continue
        card = tree / "HANDOFF.md"
        if not card.exists() and not card.is_symlink():
            continue
        inspection = {"errors": [], "warnings": [], "inspected_files": []}
        try:
            if git_output(tree, "ls-files", "-z", "--", "HANDOFF.md"):
                report["errors"].append({"code": "tracked_handoff", "worktree": str(tree),
                                         "detail": "a tracked card cannot identify a local task"})
                continue
            fields = inspect_document(tree.resolve(), "HANDOFF.md", inspection, worktree_task=True)
        except (OSError, ValueError) as exc:
            fields = {}
            inspection["errors"].append({"code": "inspection_error", "detail": str(exc)})
        for level in ("errors", "warnings"):
            report[level].extend(dict(item, worktree=str(tree)) for item in inspection[level])
        row = {key.lower(): value for key, value in fields.items()}
        row.update(worktree=str(tree), branch=data.get(b"branch", "").removeprefix("refs/heads/") or None)
        report["tasks"].append(row)
        if row.get("status") in {"blocked", "in_progress"} and row.get("task"):
            first = active_ids.setdefault(row["task"], str(tree))
            if first != str(tree):
                report["errors"].append({"code": "duplicate_task", "task": row["task"],
                                         "worktrees": [first, str(tree)]})
    report["result"] = "failed" if report["errors"] else "passed"
    return report
