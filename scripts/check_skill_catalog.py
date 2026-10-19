#!/usr/bin/env python3
"""Check that README.md lists exactly the skills under skills/."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
README = ROOT / "README.md"
START = "<!-- skills:start -->"
END = "<!-- skills:end -->"


def find_skills() -> list[Path]:
    return sorted(
        (path for path in SKILLS.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()),
        key=lambda path: path.name,
    )


def read_frontmatter(path: Path) -> dict[str, str] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return None

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[match.group(1)] = value
    return fields


def catalog(names: list[str]) -> str:
    return "\n".join([START, *[f"- `{name}`" for name in names], END])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the README catalog block")
    args = parser.parse_args()

    skills = find_skills()
    if not skills:
        print(f"error: no skills found under {SKILLS}")
        return 1

    errors: list[str] = []
    for skill in skills:
        fields = read_frontmatter(skill / "SKILL.md")
        if fields is None:
            errors.append(f"{skill.name}: missing frontmatter")
            continue
        if fields.get("name") != skill.name:
            errors.append(f"{skill.name}: name is {fields.get('name')!r}")
        if not fields.get("description"):
            errors.append(f"{skill.name}: description is empty")

    names = [skill.name for skill in skills]
    expected = catalog(names)

    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        errors.append(f"README is missing {START} / {END}")
    else:
        if args.write:
            text = re.sub(
                re.escape(START) + r".*?" + re.escape(END),
                expected,
                text,
                count=1,
                flags=re.DOTALL,
            )
            README.write_text(text, encoding="utf-8", newline="\n")
            print(f"updated {README.relative_to(ROOT)} with {len(names)} skills")
        current = re.search(re.escape(START) + r".*?" + re.escape(END), text, flags=re.DOTALL)
        if current is None or current.group(0) != expected:
            errors.append("README skill catalog is out of date; run with --write")

    if errors:
        print("skill catalog check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"ok: {len(names)} skills; frontmatter and README catalog match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
