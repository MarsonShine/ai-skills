#!/usr/bin/env python3
"""Initialize and maintain the repository harness block."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

VERSION = 1
END_MARKER = "<!-- /harness:managed -->"
START_RE = re.compile(r"<!--\s*harness:managed\s+v(\d+)\s+sha256:([0-9a-f]{64})\s*-->")
AGENTS = Path("AGENTS.md")
CLAUDE = Path("CLAUDE.md")
COPILOT = Path(".github/copilot-instructions.md")
IGNORE = Path(".harness-ignore")
SUPPORT_TEMPLATES = {
    Path("docs/status.md"): "status.md",
    Path("docs/tasks/active.md"): "active.md",
    Path(".github/pull_request_template.md"): "pull_request_template.md",
    Path("docs/harness.md"): "harness.md",
}

PROJECT_SECTION = """## Project

- Stack:
- Build:
- Test:
- Commands: `README.md`
- Boundaries:
"""


def template_dir() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here / "templates", here.parent / "templates"):
        if (candidate / "AGENTS.managed.md").is_file():
            return candidate
    raise SystemExit("error: harness templates not found next to harness.py")


def template(name: str) -> str:
    return (template_dir() / name).read_text(encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize(body: str) -> str:
    return body.replace("\r\n", "\n").strip("\n") + "\n"


def digest(body: str) -> str:
    return hashlib.sha256(normalize(body).encode("utf-8")).hexdigest()


def render(body: str) -> str:
    body = normalize(body)
    return f"<!-- harness:managed v{VERSION} sha256:{digest(body)} -->\n{body}{END_MARKER}\n"


def parse(text: str) -> dict[str, object] | None:
    match = START_RE.search(text)
    if match is None:
        return None
    end = text.find(END_MARKER, match.end())
    if end == -1:
        return None
    inner = text[match.end() : end]
    if inner.startswith("\n"):
        inner = inner[1:]
    body = normalize(inner)
    return {
        "version": int(match.group(1)),
        "hash": match.group(2),
        "body": body,
        "start": match.start(),
        "end": end + len(END_MARKER),
    }


def replace_block(text: str, body: str) -> str | None:
    parsed = parse(text)
    if parsed is None:
        return None
    return text[: int(parsed["start"])] + render(body) + text[int(parsed["end"]) :]


def insert_block(text: str, block: str) -> str:
    if not text.strip():
        return block
    head, _, rest = text.partition("\n")
    if head.startswith("# "):
        return head + "\n\n" + block + "\n" + rest.lstrip("\n")
    return block + "\n" + text


def state(path: Path) -> str:
    if not path.is_file():
        return "missing"
    parsed = parse(read(path))
    if parsed is None:
        return "no-block"
    if digest(str(parsed["body"])) != parsed["hash"]:
        return "tampered"
    if int(parsed["version"]) != VERSION:
        return "outdated"
    return "ok"


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def repo_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    result = git(Path.cwd(), "rev-parse", "--show-toplevel")
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return Path.cwd().resolve()


def in_merge(root: Path) -> bool:
    dot_git = root / ".git"
    if dot_git.is_file():
        return False
    return any(
        (dot_git / name).exists()
        for name in ("MERGE_HEAD", "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD")
    )


def is_dirty(root: Path) -> bool:
    return bool(git(root, "status", "--porcelain").stdout.strip())


def harness_doc() -> str:
    body = normalize(template("AGENTS.managed.md")).rstrip("\n")
    return template("harness.md").replace("{{AGENTS_MANAGED}}", body)


def ensure_agents(root: Path, body: str, adopt: bool) -> bool:
    path = root / AGENTS
    block = render(body)
    if not path.is_file() or not read(path).strip():
        text = "# AGENTS.md\n\n" + block + "\n" + PROJECT_SECTION
        write(path, text)
        return True
    text = read(path)
    if parse(text) is not None:
        print("AGENTS.md already contains a managed block; run sync")
        return False
    updated = insert_block(text, block)
    if re.search(r"(?m)^## Project\s*$", updated) is None:
        updated = updated.rstrip("\n") + "\n\n" + PROJECT_SECTION
    write(path, updated)
    return True


def ensure_copilot(root: Path, body: str) -> bool:
    path = root / COPILOT
    block = render(body)
    if not path.is_file():
        write(path, block)
        return True
    text = read(path)
    if parse(text) is not None:
        write(path, replace_block(text, body) or text)
        return True
    write(path, insert_block(text, block))
    return True


def ensure_claude(root: Path) -> bool:
    path = root / CLAUDE
    if not path.is_file():
        write(path, template("CLAUDE.adapter.md"))
        return True
    text = read(path)
    if "@AGENTS.md" in text:
        return False
    write(path, text.rstrip("\n") + "\n\n@AGENTS.md\n")
    return True


def ensure_support_files(root: Path) -> list[str]:
    created: list[str] = []
    for relative, name in SUPPORT_TEMPLATES.items():
        path = root / relative
        if not path.is_file() or not read(path).strip():
            content = harness_doc() if name == "harness.md" else template(name)
            write(path, content)
            created.append(str(relative))
    return created


def guard(root: Path, auto: bool) -> None:
    if (root / IGNORE).exists():
        raise SystemExit("error: .harness-ignore exists")
    if in_merge(root):
        raise SystemExit("error: merge or rebase in progress")
    if auto and is_dirty(root):
        raise SystemExit("error: auto init requires a clean working tree")


def cmd_status(root: Path) -> int:
    print(f"repository: {root}")
    print(f"AGENTS.md: {state(root / AGENTS)}")
    print(f"copilot:   {state(root / COPILOT)}")
    claude = root / CLAUDE
    if not claude.is_file():
        print("CLAUDE.md: missing")
    elif "@AGENTS.md" in read(claude):
        print("CLAUDE.md: ok")
    else:
        print("CLAUDE.md: no @AGENTS.md import")
    return 0


def cmd_check(root: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    agents_state = state(root / AGENTS)
    if agents_state in {"missing", "no-block", "tampered"}:
        errors.append(f"AGENTS.md: {agents_state}")
    elif agents_state == "outdated":
        warnings.append("AGENTS.md: baseline version is older than this engine")

    copilot_state = state(root / COPILOT)
    if copilot_state == "tampered":
        errors.append("copilot: hash mismatch")
    elif copilot_state in {"missing", "no-block"}:
        warnings.append(f"copilot: {copilot_state}")

    claude = root / CLAUDE
    if not claude.is_file():
        warnings.append("CLAUDE.md: missing")
    elif "@AGENTS.md" not in read(claude):
        warnings.append("CLAUDE.md: missing @AGENTS.md import")

    for relative in SUPPORT_TEMPLATES:
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative.as_posix()}: missing; run sync --write to restore the template")
        elif not read(path).strip():
            errors.append(f"{relative.as_posix()}: empty; run sync --write to restore the template")

    for message in warnings:
        print(f"warning: {message}")
    for message in errors:
        print(f"error: {message}")
    return 1 if errors else 0


def cmd_init(root: Path, write_changes: bool, auto: bool) -> int:
    guard(root, auto)
    agents = root / AGENTS
    if agents.is_file() and read(agents).strip():
        raise SystemExit("error: AGENTS.md already has content; use adopt")

    body = template("AGENTS.managed.md")
    planned = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", "docs/status.md", "docs/tasks/active.md", ".github/pull_request_template.md", "docs/harness.md"]
    print("would create/update:")
    for item in planned:
        print(f"- {item}")
    if not write_changes:
        print("dry run; pass --write to apply")
        return 0

    ensure_agents(root, body, adopt=False)
    ensure_copilot(root, body)
    ensure_claude(root)
    ensure_support_files(root)
    print("initialized; review the diff before committing")
    return 0


def cmd_adopt(root: Path, write_changes: bool) -> int:
    guard(root, auto=False)
    agents = root / AGENTS
    if not agents.is_file() or not read(agents).strip():
        raise SystemExit("error: AGENTS.md is missing or empty; use init")
    text = read(agents)
    if parse(text) is not None:
        print("AGENTS.md already contains a managed block; run sync")
        return 0
    body = template("AGENTS.managed.md")
    print("would add the managed block to AGENTS.md and create adapters")
    if not write_changes:
        print("dry run; pass --write to apply")
        return 0

    ensure_agents(root, body, adopt=True)
    ensure_copilot(root, body)
    ensure_claude(root)
    created = ensure_support_files(root)
    print("adopted; review the diff before committing")
    for item in created:
        print(f"- created {item}")
    return 0


def cmd_sync(root: Path, write_changes: bool) -> int:
    guard(root, auto=False)
    agents = root / AGENTS
    if not agents.is_file() or parse(read(agents)) is None:
        raise SystemExit("error: AGENTS.md has no managed block; run adopt")
    body = template("AGENTS.managed.md")
    print("would update managed blocks and restore missing or empty support documents")
    if not write_changes:
        print("dry run; pass --write to apply")
        return 0

    updated = replace_block(read(agents), body)
    write(agents, updated or "")
    copilot = root / COPILOT
    if copilot.is_file():
        text = read(copilot)
        if parse(text) is not None:
            write(copilot, replace_block(text, body) or text)
        else:
            write(copilot, insert_block(text, render(body)))
    ensure_claude(root)
    created = ensure_support_files(root)
    print("synced; review the diff before committing")
    for item in created:
        print(f"- restored {item}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "check", "init", "adopt", "sync"):
        command = sub.add_parser(name)
        command.add_argument("--root", help="repository root (defaults to the git root)")
        if name in ("init", "adopt", "sync"):
            command.add_argument("--write", action="store_true", help="apply changes")
        if name == "init":
            command.add_argument("--auto", action="store_true", help="require a clean tree")

    args = parser.parse_args()
    root = repo_root(args.root)

    if args.command == "status":
        return cmd_status(root)
    if args.command == "check":
        return cmd_check(root)
    if args.command == "init":
        return cmd_init(root, args.write, args.auto)
    if args.command == "adopt":
        return cmd_adopt(root, args.write)
    if args.command == "sync":
        return cmd_sync(root, args.write)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
