"""Measure a fixed repository-startup path without reading conversation history."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--read", action="append", default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    files = list(dict.fromkeys(["AGENTS.md", args.state, *args.read]))
    before, after = {}, {}
    for name in files:
        path = (root / name).resolve()
        path.relative_to(root)
        old = subprocess.run(["git", "-C", str(root), "show", f"{args.baseline}:{name}"],
                             capture_output=True, check=True).stdout.decode("utf-8")
        current = path.read_text(encoding="utf-8")
        for target, text in ((before, old), (after, current)):
            normalized = text.replace("\r\n", "\n")
            target[name] = {"characters": len(normalized), "lines": len(normalized.splitlines())}
    state = (root / args.state).read_text(encoding="utf-8")
    fields = {}
    for key in ("Status", "Task", "Next"):
        matches = re.findall(r"^" + key + r":[ \t]*(.+)$", state, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError(f"Cannot recover an unambiguous {key}")
        fields[key] = matches[0]
    if fields["Status"] != "idle" or fields["Task"] != "none":
        raise ValueError("The completed exercise must leave an idle current entry")
    report = {"repository": root.name, "baseline": args.baseline, "read_files": files,
              "before": before, "after": after, "recovered_state": fields,
              "before_characters": sum(item["characters"] for item in before.values()),
              "after_characters": sum(item["characters"] for item in after.values()),
              "result": "passed",
              "limits": "Deterministic startup-path inspection, not a fresh model session. Characters are not tokens; model mistakes and repeated test executions were not measured."}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
