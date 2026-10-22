"""Reject runtime environments and bytecode from an installable skills tree."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    skills = args.root.resolve() / "skills"
    if not skills.is_dir():
        parser.error("root must contain a skills directory")
    artifacts = []
    for directory, children, files in os.walk(skills, followlinks=False):
        for child in list(children):
            if child in {".venv", "venv", "__pycache__"}:
                artifacts.append((Path(directory) / child).relative_to(skills).as_posix())
                children.remove(child)
        for name in files:
            if name.endswith((".pyc", ".pyo")):
                artifacts.append((Path(directory) / name).relative_to(skills).as_posix())
    print(json.dumps({"result": "failed" if artifacts else "passed", "runtime_artifacts": sorted(artifacts)}))
    return int(bool(artifacts))


if __name__ == "__main__":
    raise SystemExit(main())
