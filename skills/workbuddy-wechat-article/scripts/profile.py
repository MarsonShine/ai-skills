"""Author profile: validation, questionnaire defaults, and loading.

The profile is deliberately small and explicit.  Every value is something the
author can confirm; nothing is inferred from their writing without permission.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised through article.py
    yaml = None  # type: ignore[assignment]


ENUMS: dict[str, tuple[str, ...]] = {
    "relation": ("self", "spouse", "daughter", "son", "parent", "pet"),
    "tone": ("warm", "plain", "witty", "gentle", "dry"),
    "person": ("first", "persona_third"),
    "sentence_len": ("short", "mixed", "long"),
    "emoji": ("none", "sparing", "liberal"),
    "scene": ("family", "travel", "daily", "anniversary", "auto"),
    "whitespace": ("tight", "normal", "airy"),
    "para_len": ("short", "mixed", "long"),
}

SCENES = ("family", "travel", "daily", "anniversary", "auto")

DEFAULT: dict[str, Any] = {
    "version": 1,
    "identity": {"name": "未署名"},
    "family": {"ok_to_write": True, "members": []},
    "topics": {"frequent": ["日常"], "never": [], "series": []},
    "voice": {
        "tone": "warm",
        "person": "first",
        "sentence_len": "mixed",
        "catchphrases": [],
        "reader_address": "你们",
        "humor": 1,
        "emoji": "sparing",
        "signature": "",
        "signoff": "",
    },
    "typesetting": {
        "scene": "daily",
        "whitespace": "normal",
        "para_len": "mixed",
        "image_ratio": "4:3",
        "prefer_blocks": [],
        "forbid_blocks": ["code"],
    },
    "taboo": {"hard_words": [], "soft_words": [], "topics": [], "avoid_tone": [], "private": []},
}

QUESTIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "name",
        "field": "identity.name",
        "question": "文章里署名是谁？用你希望读者看到的名字或昵称。",
        "default": "未署名",
    },
    {
        "id": "role_city",
        "fields": ["identity.role", "identity.city"],
        "question": "你的身份和常待的城市是什么？可以不写身份，只写城市。",
        "default": {"role": "", "city": ""},
    },
    {
        "id": "members",
        "field": "family.members",
        "question": "常写到的家人有哪些？每位给一个称呼；孩子再给年龄。",
        "default": [],
        "note": "成员格式：{relation, nickname, age?, note?}，relation 取 self/spouse/daughter/son/parent/pet。",
    },
    {
        "id": "topics",
        "field": "topics.frequent",
        "question": "你最常写的三个主题是什么？",
        "default": ["日常"],
    },
    {
        "id": "never",
        "field": "topics.never",
        "question": "哪些题材你明确不写？",
        "default": [],
    },
    {
        "id": "tone",
        "field": "voice.tone",
        "question": "你希望读起来是什么语气？warm 温暖 / plain 朴素 / witty 调侃 / gentle 轻缓 / dry 克制。",
        "default": "warm",
    },
    {
        "id": "person",
        "field": "voice.person",
        "question": "用第一人称“我”，还是以旁观口吻写“她/他”？",
        "default": "first",
    },
    {
        "id": "sentence_len",
        "field": "voice.sentence_len",
        "question": "句子习惯偏短、长短混合，还是偏长？",
        "default": "mixed",
    },
    {
        "id": "catchphrases",
        "field": "voice.catchphrases",
        "question": "你常挂在嘴边的词或口头禅是什么？最多五个。",
        "default": [],
    },
    {
        "id": "signature",
        "fields": ["voice.signature", "voice.signoff"],
        "question": "文末落款和一句告别语怎么写？",
        "default": {"signature": "", "signoff": ""},
    },
    {
        "id": "whitespace",
        "field": "typesetting.whitespace",
        "question": "版式喜欢紧、 normal 正常，还是 airy 大量留白？",
        "default": "normal",
    },
    {
        "id": "emoji",
        "field": "voice.emoji",
        "question": "表情用不用？none 不用 / sparing 少量 / liberal 常用。",
        "default": "sparing",
    },
)


class ProfileError(ValueError):
    """Raised with a field-level explanation when a profile is invalid."""


def _error(path: str, expected: str, actual: Any) -> None:
    shown = json.dumps(actual, ensure_ascii=False, default=str)
    if len(shown) > 80:
        shown = shown[:77] + "..."
    raise ProfileError(f"{path}: 期望{expected}，实际 {shown}")


def _mapping(value: Any, path: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _error(path, "对象", value)
    extra = set(value) - allowed
    if extra:
        _error(path, "只包含 " + "、".join(sorted(allowed)), sorted(extra))
    return value


def _text(value: Any, path: str, minimum: int = 0, maximum: int = 80) -> str:
    if not isinstance(value, str):
        _error(path, f"{minimum}–{maximum} 字文本", value)
    value = value.strip()
    if len(value) < minimum or len(value) > maximum:
        _error(path, f"{minimum}–{maximum} 字文本", value)
    return value


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        _error(path, "true 或 false", value)
    return value


def _integer(value: Any, path: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        _error(path, f"{low}–{high} 的整数", value)
    return value


def _strings(value: Any, path: str, maximum: int = 20, limit: int = 20) -> list[str]:
    if not isinstance(value, list) or len(value) > limit:
        _error(path, f"最多 {limit} 项文本组成的数组", value)
    result = []
    for index, item in enumerate(value):
        result.append(_text(item, f"{path}[{index}]", 1, maximum))
    return result


def validate(data: Any) -> dict[str, Any]:
    """Validate and normalise a profile mapping.

    Unknown fields are rejected instead of silently ignored: a typo in a
    hand-written profile should fail loudly before it changes the voice.
    """
    root = _mapping(
        data,
        "profile",
        {"version", "identity", "family", "topics", "voice", "typesetting", "taboo"},
    )
    version = root.get("version", 1)
    if version != 1:
        _error("version", "1", version)

    identity = _mapping(root.get("identity"), "identity", {"name", "role", "city", "bio"})
    _text(identity.get("name"), "identity.name", 1, 24)
    for key, maximum in (("role", 40), ("city", 20), ("bio", 80)):
        if key in identity:
            _text(identity[key], f"identity.{key}", 0, maximum)

    family = _mapping(root.get("family", {}), "family", {"ok_to_write", "members"})
    if "ok_to_write" in family:
        _bool(family["ok_to_write"], "family.ok_to_write")
    members = family.get("members", [])
    if not isinstance(members, list) or len(members) > 12:
        _error("family.members", "最多 12 位成员组成的数组", members)
    for index, raw in enumerate(members):
        path = f"family.members[{index}]"
        member = _mapping(raw, path, {"relation", "nickname", "age", "note"})
        relation = member.get("relation")
        if relation not in ENUMS["relation"]:
            _error(f"{path}.relation", " / ".join(ENUMS["relation"]), relation)
        _text(member.get("nickname"), f"{path}.nickname", 1, 20)
        if "age" in member:
            _integer(member["age"], f"{path}.age", 0, 120)
        elif relation in {"daughter", "son"}:
            _error(f"{path}.age", "孩子成员要填 0–120 的整数年龄", None)
        if "note" in member:
            _text(member["note"], f"{path}.note", 0, 40)

    topics = _mapping(root.get("topics"), "topics", {"frequent", "never", "series"})
    frequent = _strings(topics.get("frequent"), "topics.frequent", 20, 12)
    if not frequent:
        _error("topics.frequent", "至少一个主题", frequent)
    for key in ("never", "series"):
        if key in topics:
            _strings(topics[key], f"topics.{key}", 20, 12)

    voice = _mapping(
        root.get("voice"),
        "voice",
        {"tone", "person", "sentence_len", "catchphrases", "reader_address", "humor", "emoji", "signature", "signoff"},
    )
    for key in ("tone", "person", "sentence_len", "emoji"):
        if voice.get(key) not in ENUMS[key]:
            _error(f"voice.{key}", " / ".join(ENUMS[key]), voice.get(key))
    for key, maximum in (("reader_address", 8), ("signature", 16), ("signoff", 40)):
        if key in voice:
            _text(voice[key], f"voice.{key}", 0, maximum)
    if "catchphrases" in voice:
        _strings(voice["catchphrases"], "voice.catchphrases", 12, 10)
    if "humor" in voice:
        _integer(voice["humor"], "voice.humor", 0, 3)

    typesetting = _mapping(
        root.get("typesetting"),
        "typesetting",
        {"scene", "whitespace", "para_len", "image_ratio", "prefer_blocks", "forbid_blocks"},
    )
    for key in ("scene", "whitespace"):
        if typesetting.get(key) not in ENUMS[key]:
            _error(f"typesetting.{key}", " / ".join(ENUMS[key]), typesetting.get(key))
    if "para_len" in typesetting and typesetting["para_len"] not in ENUMS["para_len"]:
        _error("typesetting.para_len", " / ".join(ENUMS["para_len"]), typesetting["para_len"])
    if "image_ratio" in typesetting:
        _text(typesetting["image_ratio"], "typesetting.image_ratio", 1, 8)
    for key in ("prefer_blocks", "forbid_blocks"):
        if key in typesetting:
            _strings(typesetting[key], f"typesetting.{key}", 30, 20)

    taboo = _mapping(root.get("taboo", {}), "taboo", {"hard_words", "soft_words", "topics", "avoid_tone", "private"})
    for key, maximum in (("hard_words", 16), ("soft_words", 16), ("topics", 24), ("avoid_tone", 12), ("private", 24)):
        if key in taboo:
            _strings(taboo[key], f"taboo.{key}", maximum, 20)

    # Return a complete, predictable structure for downstream consumers.
    normalised = {
        "version": 1,
        "identity": {
            "name": identity["name"],
            "role": identity.get("role", ""),
            "city": identity.get("city", ""),
            "bio": identity.get("bio", ""),
        },
        "family": {"ok_to_write": family.get("ok_to_write", True), "members": members},
        "topics": {
            "frequent": frequent,
            "never": topics.get("never", []),
            "series": topics.get("series", []),
        },
        "voice": {
            "tone": voice["tone"],
            "person": voice["person"],
            "sentence_len": voice["sentence_len"],
            "catchphrases": voice.get("catchphrases", []),
            "reader_address": voice.get("reader_address", "你们"),
            "humor": voice.get("humor", 1),
            "emoji": voice["emoji"],
            "signature": voice.get("signature", ""),
            "signoff": voice.get("signoff", ""),
        },
        "typesetting": {
            "scene": typesetting["scene"],
            "whitespace": typesetting["whitespace"],
            "para_len": typesetting.get("para_len", "mixed"),
            "image_ratio": typesetting.get("image_ratio", "4:3"),
            "prefer_blocks": typesetting.get("prefer_blocks", []),
            "forbid_blocks": typesetting.get("forbid_blocks", []),
        },
        "taboo": {
            "hard_words": taboo.get("hard_words", []),
            "soft_words": taboo.get("soft_words", []),
            "topics": taboo.get("topics", []),
            "avoid_tone": taboo.get("avoid_tone", []),
            "private": taboo.get("private", []),
        },
    }
    return normalised


def load(path: str | Path) -> dict[str, Any]:
    if yaml is None:
        raise ProfileError("缺少 PyYAML，请先运行 python -m pip install PyYAML")
    source = Path(path)
    try:
        data = yaml.safe_load(source.read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise ProfileError(f"无法读取偏好文件：{error}") from error
    except yaml.YAMLError as error:
        raise ProfileError(f"偏好 YAML 格式错误：{error}") from error
    return validate(data)


def candidate_paths(explicit: str | Path | None, workdir: str | Path | None) -> list[Path]:
    paths: list[Path] = []
    if explicit:
        paths.append(Path(explicit).expanduser().resolve())
    env = os.environ.get("WECHAT_ARTICLE_PROFILE")
    if env:
        paths.append(Path(env).expanduser().resolve())
    paths.append(Path.cwd() / "profile.yaml")
    if workdir:
        paths.append(Path(workdir).expanduser().resolve() / "profile.yaml")
    paths.append(Path.home() / ".config/workbuddy-wechat/profile.yaml")
    paths.append(Path.home() / ".wagent/profile.yaml")
    unique: list[Path] = []
    for path in paths:
        if path not in unique:
            unique.append(path)
    return unique


def resolve(explicit: str | Path | None = None, workdir: str | Path | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """Return ``(profile, source)`` from the first existing candidate path."""
    if explicit:
        target = Path(explicit).expanduser().resolve()
        if not target.is_file():
            raise ProfileError(f"指定的作者档案不存在：{target}")
        return load(target), str(target)
    for path in candidate_paths(None, workdir):
        if path.is_file():
            return load(path), str(path)
    return None, None


def merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge a partial profile over defaults."""
    result = json.loads(json.dumps(base, ensure_ascii=False))
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


ANSWER_FIELDS: dict[str, Any] = {
    "name": "identity.name",
    "role": "identity.role",
    "city": "identity.city",
    "bio": "identity.bio",
    "members": "family.members",
    "ok_to_write": "family.ok_to_write",
    "topics": "topics.frequent",
    "never": "topics.never",
    "series": "topics.series",
    "tone": "voice.tone",
    "person": "voice.person",
    "sentence_len": "voice.sentence_len",
    "catchphrases": "voice.catchphrases",
    "reader_address": "voice.reader_address",
    "humor": "voice.humor",
    "emoji": "voice.emoji",
    "signature": "voice.signature",
    "signoff": "voice.signoff",
    "scene": "typesetting.scene",
    "whitespace": "typesetting.whitespace",
    "para_len": "typesetting.para_len",
    "image_ratio": "typesetting.image_ratio",
    "prefer_blocks": "typesetting.prefer_blocks",
    "forbid_blocks": "typesetting.forbid_blocks",
    "hard_words": "taboo.hard_words",
    "soft_words": "taboo.soft_words",
    "never_topics": "taboo.topics",
    "avoid_tone": "taboo.avoid_tone",
    "private": "taboo.private",
}


def _set_path(document: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    target = document
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def from_answers(answers: dict[str, Any]) -> dict[str, Any]:
    """Build a full profile from questionnaire answers or a partial profile.

    Answers may use the short questionnaire keys above or the profile paths
    themselves.  Unanswered values fall back to the defaults, and the result
    still passes the same validator as a hand-written file.
    """
    if not isinstance(answers, dict):
        raise ProfileError("问卷答案应为 JSON 对象")
    partial: dict[str, Any] = {}
    for key, value in answers.items():
        path = key if "." in key else ANSWER_FIELDS.get(key)
        if path is None:
            _error(f"answers.{key}", "问卷字段或 profile 路径", key)
        if value is None:
            continue
        _set_path(partial, path, value)
    return validate(merge(DEFAULT, partial))


def questions() -> list[dict[str, Any]]:
    return [dict(item) for item in QUESTIONS]


def example() -> str:
    return EXAMPLE.strip() + "\n"


def save(profile: dict[str, Any], path: str | Path) -> Path:
    if yaml is None:
        raise ProfileError("缺少 PyYAML，请先运行 python -m pip install PyYAML")
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, delete=False, suffix=".yaml"
        ) as handle:
            yaml.safe_dump(profile, handle, allow_unicode=True, sort_keys=False)
            temporary = Path(handle.name)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


def style_contract(profile: dict[str, Any]) -> str:
    """A compact, executable voice brief for the writing model."""
    voice = profile["voice"]
    topics = profile["topics"]
    taboo = profile["taboo"]
    members = [
        f"{member['nickname']}（{member['relation']}"
        + (f"，{member['age']}岁" if "age" in member else "")
        + "）"
        for member in profile["family"]["members"]
    ]
    lines = [
        f"署名：{profile['identity']['name']}"
        + (f"；身份：{profile['identity']['role']}" if profile["identity"]["role"] else "")
        + (f"；城市：{profile['identity']['city']}" if profile["identity"]["city"] else ""),
        f"声音：{voice['tone']} / {voice['person']} / 句长 {voice['sentence_len']} / 幽默 {voice['humor']}/3 / emoji {voice['emoji']}",
        f"常写：{'、'.join(topics['frequent'])}"
        + (f"；不写：{'、'.join(topics['never'])}" if topics["never"] else ""),
    ]
    if profile["identity"]["bio"]:
        lines.insert(1, "自述：" + profile["identity"]["bio"])
    typesetting = profile["typesetting"]
    lines.append(
        f"版式：{typesetting['scene']} / 留白 {typesetting['whitespace']}"
        + (f" / 偏好块 {'、'.join(typesetting['prefer_blocks'])}" if typesetting["prefer_blocks"] else "")
        + (f" / 禁用块 {'、'.join(typesetting['forbid_blocks'])}" if typesetting["forbid_blocks"] else "")
    )
    if members:
        lines.append("家人：" + "、".join(members))
    if voice["catchphrases"]:
        lines.append("口头禅： " + "、".join(voice["catchphrases"]))
    if taboo["hard_words"]:
        lines.append("禁词： " + "、".join(taboo["hard_words"]))
    if taboo["avoid_tone"]:
        lines.append("避免语气： " + "、".join(taboo["avoid_tone"]))
    if taboo["private"]:
        lines.append("不写进文章： " + "、".join(taboo["private"]))
    if voice["signature"] or voice["signoff"]:
        lines.append("落款：" + voice["signature"] + (" / " + voice["signoff"] if voice["signoff"] else ""))
    return "\n".join(lines)


EXAMPLE = """
version: 1
identity:
  name: 阿柯
  role: 两个孩子的妈妈 / 自由插画师
  city: 杭州
  bio: 记录家里的碎日子，和一个总在改稿的自己
family:
  ok_to_write: true
  members:
    - {relation: daughter, nickname: 豆豆, age: 6, note: 爱问为什么}
    - {relation: son, nickname: 果果, age: 2}
    - {relation: spouse, nickname: 老周}
topics:
  frequent: [亲子日常, 手冲咖啡, 家居改造]
  never: [时政, 医疗建议, 投资理财]
  series: [豆豆语录, 一周咖啡]
voice:
  tone: warm
  person: first
  sentence_len: mixed
  catchphrases: ["说真的", "你别说"]
  reader_address: 你们
  humor: 1
  emoji: sparing
  signature: 阿柯 · 在杭州
  signoff: 下次见。
typesetting:
  scene: daily
  whitespace: airy
  para_len: short
  image_ratio: "1:1"
  prefer_blocks: [photo_polaroid, margin_note]
  forbid_blocks: [code]
taboo:
  hard_words: [赋能, 闭环, 降本增效]
  soft_words: [首先, 值得注意的是]
  topics: [疾病诊断, 学校具体名称]
  avoid_tone: [说教, 带货]
  private: [豆豆的学校, 家庭住址]
"""
