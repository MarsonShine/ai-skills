"""账号人格：定位、加载、校验、问卷、文风合同。

设计要点：
1. **双通道同构**：读 YAML 与跑问卷最终产出同一个 dict，下游不关心来源。
2. **不静默纠错**：枚举值非法就报「字段 / 期望 / 实际」，绝不偷偷改成默认值。
3. **文风合同**：把人格拼成一段可执行的写作指令，而不是「写得温暖一点」这种废话。
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ENV_PROFILE = "WECHAT_MP_PROFILE"
USER_PROFILE = "~/.wagent/profile.yaml"

TONES = {
    "warm": "温和，像跟熟人说话，不端着",
    "plain": "平实，少形容词，把事情说清楚就停",
    "witty": "俏皮，偶尔自嘲，但不油滑",
    "gentle": "轻，句子短，情绪不外放",
    "dry": "克制，冷一点，几乎不抒情",
}
PERSONS = {
    "first": "第一人称「我」，写自己的所见所感",
    "persona_third": "第三人称，把「我」隐去，像旁观者记录",
}
SENTENCE_LENS = {
    "short": "以短句为主，一句一个动作",
    "mixed": "长短交替，允许突然出现一个很短的句子",
    "long": "句子偏长，允许从句和小停顿",
}
EMOJIS = {
    "none": "不用 emoji",
    "sparing": "整篇最多一两个，只放在语气最轻的地方",
    "liberal": "可以多些，但不要每段都放",
}
SCENES = {
    "auto": "按内容自动判断",
    "family": "家庭亲子",
    "travel": "旅行出门",
    "daily": "日常随笔",
    "anniversary": "纪念日时刻",
}
WHITESPACE = {
    "tight": "紧凑",
    "normal": "适中",
    "airy": "疏朗",
}

ENUMS = {
    "voice.tone": TONES,
    "voice.person": PERSONS,
    "voice.sentence_len": SENTENCE_LENS,
    "voice.emoji": EMOJIS,
    "typesetting.scene": SCENES,
    "typesetting.whitespace": WHITESPACE,
}

DEFAULT_TABOO = ["赋能", "闭环", "抓手", "底层逻辑", "颗粒度", "组合拳", "护城河"]


class ProfileError(Exception):
    """人格文件非法。CLI 映射为 exit 8。"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


# ------------------------------------------------------------------ 定位
def find(explicit: str | None = None, article_dir: str | None = None) -> tuple[Path | None, str]:
    """按优先级找人品文件，返回 (路径, 来源说明)。四路径顺序：显式 → env → 文章目录 → 用户目录。"""
    candidates: list[tuple[str | None, str]] = [
        (explicit, "--profile"),
        (os.environ.get(ENV_PROFILE), f"环境变量 {ENV_PROFILE}"),
        (str(Path(article_dir) / "profile.yaml") if article_dir else None, "文章目录"),
        (os.path.expanduser(USER_PROFILE), "用户目录"),
    ]
    for raw, source in candidates:
        if not raw:
            continue
        p = Path(raw).expanduser().resolve()
        if p.is_file():
            return p, source
    return None, "未找到"


# ------------------------------------------------------------------ 读写
def load(path: str | Path) -> dict:
    p = Path(path)
    if yaml is None:
        raise ProfileError(["缺少 PyYAML，无法读取 profile.yaml；请 pip install pyyaml"])
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ProfileError([f"YAML 语法错误（{p}）：{e}"]) from e
    if not isinstance(data, dict):
        raise ProfileError([f"profile 顶层必须是映射，实际是 {type(data).__name__}"])
    return normalize(data, source=str(p))


def save(profile: dict, path: str | Path) -> Path:
    if yaml is None:
        raise ProfileError(["缺少 PyYAML，无法写入 profile.yaml"])
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump(profile), encoding="utf-8")
    try:
        p.chmod(0o600)
    except OSError:
        pass
    return p


def dump(profile: dict) -> str:
    body = yaml.safe_dump(
        profile, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100
    )
    head = (
        "# 公众号写作人格\n"
        "# 手改这个文件即可，不用重跑问卷。改完让 agent 重新读一次。\n"
        "# 枚举取值见 scripts/profile.py 顶部 TONES / PERSONS / SENTENCE_LENS / EMOJIS / SCENES。\n\n"
    )
    return head + body


# ------------------------------------------------------------------ 校验
def normalize(data: dict, source: str = "input") -> dict:
    """补默认值 + 校验枚举 + 结构定型。非法立即抛出，不静默纠错。"""
    errors: list[str] = []

    def section(name: str) -> dict:
        v = data.get(name)
        if v is None:
            return {}
        if not isinstance(v, dict):
            errors.append(f"{name}: 期望映射，实际 {type(v).__name__}")
            return {}
        return v

    identity = section("identity")
    family = section("family")
    topics = section("topics")
    voice = section("voice")
    typesetting = section("typesetting")
    taboo = section("taboo")

    # 枚举校验
    for key, table in ENUMS.items():
        sec, field = key.split(".")
        holder = {"identity": identity, "voice": voice, "typesetting": typesetting}[sec]
        if field in holder and holder[field] not in table:
            errors.append(
                f"{key}: 期望 {'/'.join(table)} 之一，实际 {holder[field]!r}"
            )

    # 列表字段
    def as_list(holder: dict, field: str, where: str) -> list:
        v = holder.get(field)
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            errors.append(f"{where}.{field}: 期望列表，实际 {type(v).__name__}")
            return []
        return [str(x).strip() for x in v if str(x).strip()]

    members_in = family.get("members") or []
    if not isinstance(members_in, list):
        errors.append("family.members: 期望列表")
        members_in = []
    members = []
    for i, m in enumerate(members_in):
        if not isinstance(m, dict):
            errors.append(f"family.members[{i}]: 期望映射")
            continue
        age = m.get("age")
        if age is not None:
            try:
                age = int(age)
            except (TypeError, ValueError):
                errors.append(f"family.members[{i}].age: 期望整数，实际 {age!r}")
                age = None
        if not m.get("nickname"):
            errors.append(f"family.members[{i}].nickname: 必填")
            continue
        members.append(
            {
                "nickname": str(m["nickname"]).strip(),
                "role": str(m.get("role") or "").strip(),
                "age": age,
            }
        )

    profile = {
        "identity": {
            "name": str(identity.get("name") or "").strip(),
            "city": str(identity.get("city") or "").strip(),
            "signature": str(identity.get("signature") or "").strip(),
            "bio": str(identity.get("bio") or "").strip(),
        },
        "family": {"members": members},
        "topics": {
            "write": as_list(topics, "write", "topics"),
            "avoid": as_list(topics, "avoid", "topics"),
            "series": as_list(topics, "series", "topics"),
        },
        "voice": {
            "tone": voice.get("tone") or "warm",
            "person": voice.get("person") or "first",
            "sentence_len": voice.get("sentence_len") or "mixed",
            "emoji": voice.get("emoji") or "none",
            "catchphrases": as_list(voice, "catchphrases", "voice"),
            "habits": as_list(voice, "habits", "voice"),
        },
        "typesetting": {
            "scene": typesetting.get("scene") or "auto",
            "whitespace": typesetting.get("whitespace") or "normal",
            "image_density": typesetting.get("image_density") or "normal",
        },
        "taboo": {
            "hard_words": as_list(taboo, "hard_words", "taboo") or list(DEFAULT_TABOO),
            "private": as_list(taboo, "private", "taboo"),
            "never_mention": as_list(taboo, "never_mention", "taboo"),
        },
        "_meta": {"source": source},
    }

    if not profile["identity"]["name"]:
        errors.append("identity.name: 必填（写作者怎么称呼自己）")

    if errors:
        raise ProfileError(errors)
    return profile


# ------------------------------------------------------------------ 问卷
QUESTIONS: list[dict] = [
    {
        "key": "identity.name",
        "q": "你希望读者怎么称呼你？（文章里会用到，比如「阿柯」）",
        "type": "text",
        "required": True,
    },
    {
        "key": "identity.city",
        "q": "你在哪个城市？常写的地方感会来自这里。",
        "type": "text",
        "default": "",
    },
    {
        "key": "family.members",
        "q": "家里都有谁？逐个说：昵称、关系、几岁（孩子写年龄，成年的可以不写）。没有就跳过。",
        "type": "list",
        "fields": ["nickname", "role", "age"],
        "default": [],
    },
    {
        "key": "topics.write",
        "q": "你常写什么？说三五个就行，越具体越好（「孩子说错话」比「亲子」好）。",
        "type": "list",
        "default": [],
    },
    {
        "key": "topics.avoid",
        "q": "有什么题材你绝对不写？（比如育儿干货、鸡汤、蹭热点）",
        "type": "list",
        "default": [],
    },
    {
        "key": "voice.tone",
        "q": "你说话是什么调子？",
        "type": "enum",
        "table": TONES,
        "default": "warm",
    },
    {
        "key": "voice.person",
        "q": "用第几人称写？",
        "type": "enum",
        "table": PERSONS,
        "default": "first",
    },
    {
        "key": "voice.sentence_len",
        "q": "你的句子习惯是偏短、长短混着，还是偏长？",
        "type": "enum",
        "table": SENTENCE_LENS,
        "default": "mixed",
    },
    {
        "key": "voice.catchphrases",
        "q": "有没有你反复会用的词或句式？（写作者的口头禅，是最像本人的东西）",
        "type": "list",
        "default": [],
    },
    {
        "key": "identity.signature",
        "q": "文章末尾怎么落款？可以写「阿柯 · 在杭州」，也可以留空。",
        "type": "text",
        "default": "",
    },
    {
        "key": "typesetting.scene+whitespace",
        "q": "版式偏好：主要写哪类内容（家庭亲子/旅行出门/日常随笔/纪念日），以及要紧凑还是疏朗？",
        "type": "pair",
        "keys": ["typesetting.scene", "typesetting.whitespace"],
        "tables": [SCENES, WHITESPACE],
        "default": ["daily", "normal"],
    },
    {
        "key": "voice.emoji+taboo.hard_words",
        "q": "emoji 用不用？还有哪些词你看到就烦（会进禁用词表）？",
        "type": "pair",
        "keys": ["voice.emoji", "taboo.hard_words"],
        "tables": [EMOJIS, None],
        "default": ["none", list(DEFAULT_TABOO)],
    },
]


def questions_payload() -> dict:
    """给 agent 的问卷描述。agent 在对话里问，收集完再调 init --answers。"""
    out = []
    for q in QUESTIONS:
        item = {
            "key": q["key"],
            "question": q["q"],
            "type": q["type"],
            "default": q.get("default"),
        }
        if q.get("table"):
            item["options"] = {k: v for k, v in q["table"].items()}
        if q.get("tables"):
            item["options"] = [
                (list(t.keys()) if t else "free")
                for t in q["tables"]
            ]
        if q.get("fields"):
            item["fields"] = q["fields"]
        out.append(item)
    return {
        "ok": True,
        "mode": "questionnaire",
        "count": len(out),
        "questions": out,
        "next": "收集完答案后执行 init --answers answers.json --out <path>",
    }


def from_answers(answers: dict) -> dict:
    """把问卷答案映射成 profile dict。缺项用默认值，不报错（问卷允许跳过）。"""
    data: dict = {
        "identity": {},
        "family": {"members": answers.get("family.members") or []},
        "topics": {
            "write": answers.get("topics.write") or [],
            "avoid": answers.get("topics.avoid") or [],
        },
        "voice": {
            "tone": answers.get("voice.tone") or "warm",
            "person": answers.get("voice.person") or "first",
            "sentence_len": answers.get("voice.sentence_len") or "mixed",
            "emoji": answers.get("voice.emoji") or "none",
            "catchphrases": answers.get("voice.catchphrases") or [],
        },
        "typesetting": {
            "scene": answers.get("typesetting.scene") or "daily",
            "whitespace": answers.get("typesetting.whitespace") or "normal",
        },
        "taboo": {"hard_words": answers.get("taboo.hard_words") or list(DEFAULT_TABOO)},
    }
    for f in ("name", "city", "signature"):
        if answers.get(f"identity.{f}"):
            data["identity"][f] = answers[f"identity.{f}"]
    return normalize(data, source="questionnaire")


def template() -> str:
    """手填模板：每个字段都有注释，填完即用。"""
    return """# 公众号写作人格（手填版）
# 放到 ~/.wagent/profile.yaml，或与文章同目录，或 --profile 指定。
# 不确定的字段删掉即可，会自动取默认值。

identity:
  name: 阿柯              # 必填。读者怎么称呼你
  city: 杭州
  signature: 阿柯 · 在杭州   # 文末落款，留空则不加
  bio: 记录豆豆长大的日常

family:
  members:                # 没有孩子/不写家人就留空列表
    - nickname: 豆豆
      role: 女儿
      age: 6

topics:
  write:                  # 常写什么，越具体越好
    - 孩子说错话
    - 家里的一顿饭
    - 出门走走
  avoid:                  # 绝对不写
    - 育儿干货
    - 鸡汤
  series: []              # 连载栏目名，可留空

voice:
  tone: warm              # warm / plain / witty / gentle / dry
  person: first           # first / persona_third
  sentence_len: mixed     # short / mixed / long
  catchphrases:           # 口头禅，反复用，别换同义词
    - 慢慢地
  emoji: sparing          # none / sparing / liberal

typesetting:
  scene: daily            # auto / family / travel / daily / anniversary
  whitespace: airy        # tight / normal / airy
  image_density: normal   # sparse / normal / dense

taboo:
  hard_words:             # 出现就扣分
    - 赋能
    - 闭环
    - 抓手
  private:                # 不写进正文的私人信息
    - 小区名
"""


# ------------------------------------------------------------------ 文风合同
def contract(profile: dict, scene: str | None = None) -> str:
    """把人格拼成可执行的写作指令。给 llm 与 rewrite 共用。"""
    p = profile or {}
    ident = p.get("identity") or {}
    voice = p.get("voice") or {}
    ts = p.get("typesetting") or {}
    taboo = p.get("taboo") or {}

    lines: list[str] = []
    name = ident.get("name") or "作者"
    lines.append(f"- 写作者：{name}" + (f"，常住{ident['city']}" if ident.get("city") else ""))
    if ident.get("bio"):
        lines.append(f"- 账号简介：{ident['bio']}")

    members = (p.get("family") or {}).get("members") or []
    if members:
        def _one(m):
            inner = "，".join(
                x for x in (m.get("role") or "", f"{m['age']}岁" if m.get("age") else "") if x
            )
            return f"{m['nickname']}（{inner}）" if inner else m["nickname"]

        who = "、".join(_one(m) for m in members)
        lines.append(f"- 常出现的人：{who}；提到孩子时用昵称，不写全名")

    tone = voice.get("tone") or "warm"
    lines.append(f"- 语气：{TONES.get(tone, tone)}")
    person = voice.get("person") or "first"
    lines.append(f"- 人称：{PERSONS.get(person, person)}")
    sl = voice.get("sentence_len") or "mixed"
    lines.append(f"- 句子节奏：{SENTENCE_LENS.get(sl, sl)}")
    if voice.get("catchphrases"):
        lines.append(
            "- 口头禅（允许在同一篇里重复出现，不要为了变化而换同义词）："
            + "、".join(voice["catchphrases"])
        )
    if voice.get("habits"):
        lines.append("- 写作习惯：" + "；".join(voice["habits"]))
    emoji = voice.get("emoji") or "none"
    lines.append(f"- emoji：{EMOJIS.get(emoji, emoji)}")

    topics = p.get("topics") or {}
    if topics.get("write"):
        lines.append("- 常写：" + "、".join(topics["write"]))
    avoid = list(topics.get("avoid") or []) + list(taboo.get("never_mention") or [])
    if avoid:
        lines.append("- 不写：" + "、".join(avoid))
    if taboo.get("hard_words"):
        lines.append("- 禁用词（一个都不要出现）：" + "、".join(taboo["hard_words"]))
    if taboo.get("private"):
        lines.append("- 隐私红线（不写进正文）：" + "、".join(taboo["private"]))

    sc = scene or ts.get("scene") or "auto"
    ws = ts.get("whitespace") or "normal"
    lines.append(f"- 版式：{SCENES.get(sc, sc)}，留白{WHITESPACE.get(ws, ws)}")

    return "\n".join(lines)


def contract_rules(profile: dict) -> str:
    """比 contract 更硬的约束段，附在 prompt 末尾。"""
    avoid = (profile.get("topics") or {}).get("avoid") or []
    hard = (profile.get("taboo") or {}).get("hard_words") or []
    rules = [
        "1. 只写用户给出的事实。用户没说的细节不要编；需要细节时留占位符让人补。",
        "2. 不总结、不升华、不写「这就是生活的意义」这类收尾。",
        "3. 不平铺三段排比，不用「不是……而是……」，不用破折号制造停顿。",
        "4. 保留口语的毛边：允许一句话只有四五个字，允许句子之间不衔接。",
        "5. 数字、时间、地点、原话照抄，不要「大约」「左右」化。",
    ]
    if avoid:
        rules.append(f"6. 不碰这些题材：{'、'.join(avoid)}。")
    if hard:
        rules.append(f"7. 禁用词：{'、'.join(hard)}。")
    return "\n".join(rules)
