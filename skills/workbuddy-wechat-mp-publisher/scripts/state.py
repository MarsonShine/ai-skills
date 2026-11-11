"""幂等账本：内容指纹 → media_id。

为什么需要：同一篇稿子重跑一次就多一条草稿，几次之后草稿箱全是重复的，
人还得手动删。这里用「标题 + 正文 + 图片」的指纹记账：
同指纹重跑直接返回原 media_id，改了内容才走 draft/update。
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

STATE_NAME = "state.json"


def fingerprint(title: str, content: str, images: list[str]) -> str:
    """只取内容本身。时间戳不参与，否则每次都算新稿。"""
    h = hashlib.sha256()
    h.update((title or "").strip().encode("utf-8"))
    h.update(b"\x00")
    h.update((content or "").encode("utf-8"))
    for s in images or []:
        h.update(b"\x00")
        h.update(str(s).encode("utf-8"))
    return h.hexdigest()[:16]


def _path(workdir: str | Path) -> Path:
    return Path(workdir) / STATE_NAME


def load(workdir: str | Path) -> dict:
    p = _path(workdir)
    if not p.is_file():
        return {"articles": {}}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(d.get("articles"), dict):
            return {"articles": {}}
        return d
    except (ValueError, OSError):
        return {"articles": {}}


def lookup(workdir: str | Path, fp: str) -> dict | None:
    return load(workdir)["articles"].get(fp)


def record(workdir: str | Path, fp: str, media_id: str, **extra) -> dict:
    p = _path(workdir)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = load(workdir)
    entry = {
        "media_id": media_id,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        **extra,
    }
    data["articles"][fp] = entry
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def forget(workdir: str | Path, fp: str) -> bool:
    p = _path(workdir)
    data = load(workdir)
    if fp in data["articles"]:
        data["articles"].pop(fp)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    return False
