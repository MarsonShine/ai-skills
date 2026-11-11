"""Load hand-written YAML or save the same fields from a conversation."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

import yaml


def validate(data):
    fields = {"person", "tone", "author", "avoid", "whitespace", "scene"}
    if not isinstance(data, dict) or set(data) - fields:
        raise ValueError("偏好应为 YAML 映射，可用字段为 " + ", ".join(sorted(fields)))
    for key, value in data.items():
        if key == "avoid":
            if not isinstance(value, list) or not all(isinstance(w, str) and w.strip() for w in value):
                raise ValueError("avoid 应为非空词语组成的列表")
        elif not isinstance(value, str):
            raise ValueError(f"{key} 应为文本")
    for key, choices in {"person": ("first", "third"), "whitespace": ("tight", "normal", "airy"),
                         "scene": ("family", "travel", "daily", "anniversary", "auto")}.items():
        if key in data and data[key] not in choices:
            raise ValueError(f"{key} 可选 " + ", ".join(choices))
    if len(data.get("author", "")) > 16:
        raise ValueError("author 最多 16 字")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--save", action="store_true", help="read confirmed preferences as JSON from stdin")
    args = parser.parse_args()
    if not args.save:
        print(json.dumps(validate(yaml.safe_load(args.file.read_text(encoding="utf-8-sig")))))
        return
    data = validate(json.load(sys.stdin))
    args.file.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.file.parent, delete=False) as target:
            tmp = Path(target.name)
            yaml.safe_dump(data, target, allow_unicode=True, sort_keys=False)
        os.replace(tmp, args.file)
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    print(json.dumps({"ok": True, "path": str(args.file.resolve())}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, yaml.YAMLError) as error:
        sys.exit(str(error))
