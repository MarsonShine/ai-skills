"""去 AI 味诊断：纯规则 + 统计，同输入同输出，不调模型。

三条设计原则（缺一条就会翻车）：
1. **聚集才判罚**：单个信号不算数。一个破折号、一处排比本身什么都不是，
   同一个窗口里信号 ≥3 且跨 ≥2 个类别才扣分。
2. **正向指标同样计分**：写得干净但没活人气息，一样一眼假。只靠「不犯错」
   拿不到高分，否则会把文章改得又干净又死。
3. **keep 清单**：把「看着像问题但建议保留」的位置列出来并说明理由。
   短句、毛边、没解决的矛盾，是人的呼吸，不是缺陷。

文档级统计量（句长节奏、段落等长、空洞结尾）不参与「聚集」判定——
它们本身就是聚合指标，不存在「单点误伤」问题，这点在实现里显式区分。
"""

from __future__ import annotations

import re
import statistics
from collections import OrderedDict

# ------------------------------------------------------------------ 词表
# 硬禁：出现即扣分，这类词几乎只会出现在 PPT 和 AI 稿里
HARD_WORDS = [
    "赋能", "闭环", "抓手", "底层逻辑", "颗粒度", "组合拳", "护城河",
    "顶层设计", "降本增效", "沉浸式", "全链路", "生态位", "颠覆式",
]
# 慎用：单独出现没问题，密度高或成簇才是毛病
SOFT_WORDS = [
    "首先", "其次", "再次", "最后", "综上", "总而言之", "值得注意的是",
    "众所周知", "显而易见", "某种程度上", "不难发现", "由此可见",
    "在这个快节奏的时代", "让我们一起",
]

# 中文 AI 稿里信号最强的两个：破折号、否定式排比
NEG_PATTERNS = [
    r"不是[^。！？；\n]{1,24}而是",
    r"不只是[^。！？；\n]{1,24}更是",
    r"不仅是[^。！？；\n]{1,24}更是",
    r"并非[^。！？；\n]{1,24}而是",
    r"与其说[^。！？；\n]{1,24}不如说",
]

EMPTY_ENDINGS = [
    "这就是生活", "生活就是这样", "愿我们都能", "愿你", "让我们", "希望我们",
    "在这个", "其实人生", "人生就是", "时间会告诉我们", "一切都会",
    "值得被记住", "都值得", "才是最重要的", "才是最珍贵的",
]

# 正向信号的近似词表。不求语言学准确，只求稳定可解释。
_ACTION_VERBS = (
    "走|跑|蹲|站|坐|躺|抱|背|牵|拎|提|推|拉|拧|塞|翻|摸|捏|敲|踢|踩|"
    "咬|嚼|咽|喝|吃|洗|擦|扫|晾|叠|贴|挂|数|指|喊|叫|应|笑|哭|叹|点头|摇头"
)
_SENSORY = (
    "味道|气味|香|腥|甜|咸|苦|酸|涩|烫|凉|冷|热|暖|软|硬|糙|黏|湿|"
    "响|静|吵|闷|亮|暗|刺眼|晃眼|发白"
)
_TIME = (
    r"\d{1,2}[:：]\d{2}|\d{1,2}\s*点|第[一二三四五六七八九十\d]+天|"
    r"早上|清早|上午|中午|下午|傍晚|夜里|半夜|凌晨|周末|昨天|前天"
)
_PLACE = (
    r"[\u4e00-\u9fa5]{2,4}(?:公园|路|街|巷|站|店|馆|河|湖|山|桥|市场|超市|医院|学校|小区)"
)
_NUM = r"\d+(?:\.\d+)?|[一二三四五六七八九十百千万两]+(?:块|元|岁|天|年|月|日|次|个|人|只|条|件|张|页|分钟|秒|斤|米|公里|层)"

RE_DASH = re.compile(r"—{1,2}|――")
RE_NUM = re.compile(_NUM)
RE_TIME = re.compile(_TIME)
RE_PLACE = re.compile(_PLACE)
RE_LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}")
RE_ACTION = re.compile(_ACTION_VERBS)
RE_SENSORY = re.compile(_SENSORY)
RE_SENT = re.compile(r"[^。！？!?…\n]+[。！？!?…]*")
RE_QUOTED = re.compile(r"[「『“\"][^」』”\"]{1,60}[」』”\"]")

# 判罚权重与类别上限
WEIGHTS = {
    "hard_word": 4.0,
    "soft_word": 1.5,
    "dash": 2.0,
    "neg_paral": 3.0,
    "triple": 2.5,
}
CAPS = {"words": 25.0, "rhythm": 20.0, "rhetoric": 20.0, "structure": 15.0, "ending": 10.0}
# 可单类别成簇的强信号（仍需同类 ≥2）
STRONG_CATS = {"words", "rhetoric"}

BANDS = [
    (85, "人味足"),
    (70, "可用"),
    (55, "明显 AI 味"),
    (0, "机器味重"),
]

# 正文块里参与诊断的字段
TEXT_TYPES = {
    "p": ["text"],
    "lead": ["text"],
    "quote": ["text"],
    "footer": ["text"],
    "drop_cap": ["text"],
    "kid_quote": ["text"],
    "letter_paper": ["text"],
    "callout": ["items"],
    "list": ["items"],
}


# ------------------------------------------------------------------ 切分
def split_sentences(text: str) -> list[tuple[str, int, int]]:
    """切句并保留原文偏移，供定点重写切片用。"""
    out = []
    for m in RE_SENT.finditer(text or ""):
        seg = m.group(0)
        if seg.strip():
            out.append((seg, m.start(), m.end()))
    return out


def iter_fields(blocks: list[dict]):
    """产出 (block_index, field_path, text, kind)。kind 用于区分 list/callout 条目。"""
    for bi, b in enumerate(blocks or []):
        kind = (b.get("type") or "p").lower()
        fields = TEXT_TYPES.get(kind)
        if not fields:
            continue
        for f in fields:
            v = b.get(f)
            if isinstance(v, str) and v.strip():
                yield bi, f, v, kind
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    t = item.get("text") if isinstance(item, dict) else item
                    if isinstance(t, str) and t.strip():
                        yield bi, f"{f}[{i}]", t, kind


# ------------------------------------------------------------------ 统计
# 「去了公园」「到了一个地方」这类不是细节，是被抽干的场景。
# 地名前若是这些词，说明它只是泛指，不计分。
PLACE_STOP = (
    "去了", "来到", "到了", "回到", "走进", "这个", "那个", "一个", "座",
    "附近", "旁边", "前面", "后面", "外面", "里面", "很多", "其他", "各种",
)


# 「一个瞬间」「一场马拉松」是虚指，不是细节。
NUM_STOP = {"一场", "一个", "一种", "一些", "一样", "一起", "一点", "一切", "一直", "一半"}


def count_num(text: str) -> int:
    return sum(1 for m in RE_NUM.findall(text) if m not in NUM_STOP)


def count_place(text: str) -> int:
    n = 0
    for m in RE_PLACE.finditer(text):
        head = m.group(0)[:-2]
        if head and any(head.startswith(s) for s in PLACE_STOP):
            continue
        n += 1
    return n


def detail_density(text: str) -> float:
    """细节密度：每百字的加权具体物数量。AI 稿的典型特征就是这里接近 0。"""
    if not text:
        return 0.0
    n = len(text)
    score = (
        count_num(text) * 1.0
        + len(RE_TIME.findall(text)) * 1.0
        + count_place(text) * 1.2
        + len(RE_LATIN.findall(text)) * 1.2
        + len(RE_ACTION.findall(text)) * 0.6
        + len(RE_SENSORY.findall(text)) * 0.8
    )
    return round(score / max(n, 1) * 100, 2)


def _cv(values: list[int]) -> float:
    if len(values) < 2:
        return 1.0
    mean = statistics.fmean(values)
    if mean == 0:
        return 1.0
    return statistics.pstdev(values) / mean


def _triple_clusters(sentence: str) -> list[str]:
    """三连排比的近似识别：按顿号/逗号切子句，滑窗取 3，长度相近且首尾字相同则算。

    不做句法分析，只抓「等长 + 同构」这个表面特征，宁可漏判也不误伤。
    """
    parts = [p.strip(" 。！？…") for p in re.split(r"[、，,]", sentence)]
    parts = [p for p in parts if 2 <= len(p) <= 10]
    out = []
    for i in range(len(parts) - 2):
        w = parts[i : i + 3]
        lens = [len(x) for x in w]
        if max(lens) - min(lens) > 2:
            continue
        same_head = len({x[0] for x in w}) == 1
        same_tail = len({x[-1] for x in w}) == 1
        if same_head or same_tail:
            out.append("、".join(w))
    return out


# ------------------------------------------------------------------ 诊断
def diagnose(doc: dict, profile: dict | None = None, scene: str | None = None) -> dict:
    blocks = doc.get("blocks") or []
    profile = profile or {}
    whitelist = set((profile.get("topics") or {}).get("write") or [])
    whitelist |= set(profile.get("_whitelist") or [])

    sentences: list[dict] = []
    for bi, field, text, kind in iter_fields(blocks):
        for si, (seg, st, en) in enumerate(split_sentences(text)):
            sentences.append(
                {
                    "sid": f"{bi}:{field}:{si}",
                    "block": bi,
                    "field": field,
                    "idx": si,
                    "start": st,
                    "end": en,
                    "text": seg,
                    "kind": kind,
                    "detail": detail_density(seg),
                    "quoted": bool(RE_QUOTED.fullmatch(seg.strip())),
                }
            )

    body = "".join(s["text"] for s in sentences)
    chars = len(re.sub(r"\s", "", body))
    raw: list[dict] = []   # 句子级信号
    doclevel: list[dict] = []  # 文档级指标

    # ---- 1. 词表
    for s in sentences:
        for w in HARD_WORDS:
            if w in s["text"] and w not in whitelist:
                raw.append(_sig(s, "hard_word", "words", 2, w, f"「{w}」是硬禁套话"))
        hits = [w for w in SOFT_WORDS if w in s["text"]]
        for w in hits:
            raw.append(_sig(s, "soft_word", "words", 1, w, f"「{w}」是模板化承接词"))

    # 慎用词密度：>2/千字才单独计，否则由聚集规则兜
    soft_n = sum(1 for x in raw if x["kind"] == "soft_word")
    soft_density = soft_n / max(chars, 1) * 1000
    if soft_density <= 2:
        raw = [x for x in raw if x["kind"] != "soft_word"]

    # 套话覆盖率：通篇靠模板词串起来，是 AI 稿最典型的整体特征。
    # 单看每个词都不重，合起来才致命，所以作为文档级指标单列。
    if sentences:
        hit_sids = {x["sid"] for x in raw if x["category"] == "words"}
        cover = len(hit_sids) / len(sentences)
        if cover >= 0.4 and len(hit_sids) >= 3:
            doclevel.append(
                {
                    "kind": "filler_cover",
                    "category": "words",
                    "weight": 8.0,
                    "why": f"{cover:.0%} 的句子含套话承接词（{len(hit_sids)}/{len(sentences)}）",
                    "sid": None,
                }
            )

    # ---- 2. 句长节奏（文档级）
    lens = [len(re.sub(r"\s", "", s["text"])) for s in sentences]
    rhythm_issues = []
    if chars >= 120 and len(lens) >= 6:
        cv = _cv(lens)
        if cv < 0.32:
            rhythm_issues.append(
                ("rhythm", "rhythm_even", 8.0, f"句长过于均匀（CV={cv:.2f}，阈值 0.32）")
            )
        flat = 0
        for i in range(len(lens) - 3):
            w = lens[i : i + 4]
            if max(w) - min(w) <= 3:
                flat += 1
        if flat >= 3:
            rhythm_issues.append(
                ("rhythm", "rhythm_flat", 6.0, f"有 {flat} 处连续 4 句长度差 ≤3 字，读起来发板")
            )
    for cat, kind, w, why in rhythm_issues:
        doclevel.append({"kind": kind, "category": cat, "weight": w, "why": why, "sid": None})

    # ---- 3. 破折号
    for s in sentences:
        n = len(RE_DASH.findall(s["text"]))
        if n >= 2:
            raw.append(_sig(s, "dash", "rhetoric", 2, "——", f"单句 {n} 个破折号"))
    dash_total = len(RE_DASH.findall(body))
    dash_density = dash_total / max(chars, 1) * 100
    if dash_density > 0.33 and dash_total >= 2:
        doclevel.append(
            {
                "kind": "dash_dense",
                "category": "rhetoric",
                "weight": 3.0,
                "why": f"破折号密度 {dash_density:.2f}/百字（阈值 0.33），全文 {dash_total} 处",
                "sid": None,
            }
        )

    # ---- 4. 否定式排比
    for s in sentences:
        for pat in NEG_PATTERNS:
            m = re.search(pat, s["text"])
            if m:
                raw.append(
                    _sig(s, "neg_paral", "rhetoric", 3, m.group(0), "「不是……而是……」式排比")
                )

    # ---- 5. 三连排比
    for s in sentences:
        for frag in _triple_clusters(s["text"]):
            raw.append(_sig(s, "triple", "rhetoric", 2.5, frag, f"三连排比：{frag}"))

    # ---- 6. 段落等长（文档级）
    paras = [len(re.sub(r"\s", "", s["text"])) for s in sentences if s["kind"] in ("p", "lead")]
    if len(paras) >= 4:
        rng = max(paras) - min(paras)
        mean = statistics.fmean(paras)
        if mean and rng / mean < 0.22:
            doclevel.append(
                {
                    "kind": "para_equal",
                    "category": "structure",
                    "weight": 6.0,
                    "why": f"{len(paras)} 段长度几乎一致（极差/均值={rng / mean:.2f}）",
                    "sid": None,
                }
            )

    # ---- 7. 空洞结尾
    tail = [s for s in sentences if s["kind"] in ("p", "lead", "footer")]
    if tail:
        last = tail[-1]
        hit = next((w for w in EMPTY_ENDINGS if w in last["text"]), None)
        if hit and last["detail"] < 1.0:
            # 结尾套话是「位置确定、语义明确」的信号，不走聚集判定：
            # 一句结尾升华就是一句结尾升华，不存在单点误伤。
            # 但保留 sid，让定点重写能定位到这一句。
            doclevel.append(
                {
                    "kind": "empty_end",
                    "category": "ending",
                    "weight": 10.0,
                    "why": f"结尾是套话「{hit}」，且没有任何具体物",
                    "sid": last["sid"],
                    "text": last["text"],
                    "word": hit,
                }
            )

    # ---- 聚类判罚
    issues, keep, clusters = _cluster(raw, sentences, doclevel)

    # ---- 正向指标
    positive = _positive(body, sentences, scene)

    # ---- 打分
    penalty = {k: 0.0 for k in CAPS}
    for c in clusters:
        for cat, v in c["by_category"].items():
            penalty[cat] = min(CAPS[cat], penalty[cat] + v)
    ai_score = max(0.0, 100.0 - sum(penalty.values()))
    human_score = positive["score"]
    final = 0.6 * ai_score + 0.4 * human_score
    band = _band(final)
    if human_score < 40 and band[0] > 55:
        # 干净但没活人气息：强制降一档
        band = _band(max(0.0, band[0] - 1))
        positive["gate"] = "human_score < 40，强制降档"

    # 分档是给人看的，动作是给 agent 用的。结尾升华这种单点问题
    # 分数上不痛不痒（只扣 10 分），但读者一眼能看出来，必须建议改。
    recommend = "rewrite" if (final < 75 or any(i["category"] == "ending" for i in issues)) else "pass"

    return {
        "ok": True,
        "recommend": recommend,
        "scores": {
            "ai": round(ai_score, 1),
            "human": round(human_score, 1),
            "final": round(final, 1),
            "band": band[1],
            "penalty": {k: round(v, 1) for k, v in penalty.items()},
        },
        "issues": issues,
        "clusters": clusters,
        "keep": keep,
        "positive": positive,
        "stats": {
            "chars": chars,
            "sentences": len(sentences),
            "blocks": len(blocks),
            "soft_density": round(soft_density, 2),
            "dash_density": round(dash_density, 2),
        },
    }


def _sig(s: dict, kind: str, cat: str, weight: float, word: str, why: str) -> dict:
    return {
        "sid": s["sid"],
        "block": s["block"],
        "field": s["field"],
        "start": s["start"],
        "end": s["end"],
        "text": s["text"],
        "kind": kind,
        "category": cat,
        "weight": weight,
        "word": word,
        "why": why,
    }


def _cluster(raw: list[dict], sentences: list[dict], doclevel: list[dict]):
    """窗口内 ≥3 信号且跨 ≥2 类别才判罚；强类别可单类别成簇但需 ≥2 条。

    未成簇的句子进 keep[]，并给出「为什么不动它」。
    """
    by_window: "OrderedDict[int, list[dict]]" = OrderedDict()
    for sig in raw:
        by_window.setdefault(sig["block"] // 2, []).append(sig)

    clusters: list[dict] = []
    penalized_sids: set[str] = set()

    for win, sigs in by_window.items():
        cats = {x["category"] for x in sigs}
        if len(sigs) >= 3 and len(cats) >= 2:
            clusters.append(
                {
                    "window": f"block {win * 2}-{win * 2 + 1}",
                    "count": len(sigs),
                    "categories": sorted(cats),
                    "penalty": round(sum(x["weight"] for x in sigs), 1),
                    "by_category": {c: round(sum(x["weight"] for x in sigs if x["category"] == c), 1) for c in sorted(cats)},
                    "why": f"窗口内 {len(sigs)} 个信号，跨 {len(cats)} 类",
                }
            )
            penalized_sids |= {x["sid"] for x in sigs}
            continue
        # 强类别单独成簇：同类别 ≥2 条
        for cat in STRONG_CATS & cats:
            same = [x for x in sigs if x["category"] == cat]
            if len(same) >= 2:
                clusters.append(
                    {
                        "window": f"block {win * 2}-{win * 2 + 1}",
                        "count": len(same),
                        "categories": [cat],
                        "penalty": round(sum(x["weight"] for x in same), 1),
                        "by_category": {cat: round(sum(x["weight"] for x in same), 1)},
                        "why": f"{cat} 类强信号 {len(same)} 条同簇",
                    }
                )
                penalized_sids |= {x["sid"] for x in same}

    for d in doclevel:
        clusters.append(
            {
                "window": "全文",
                "count": 1,
                "categories": [d["category"]],
                "penalty": d["weight"],
                "by_category": {d["category"]: d["weight"]},
                "why": d["why"],
            }
        )
        if d.get("sid"):
            penalized_sids.add(d["sid"])

    issues = []
    for sig in raw:
        if sig["sid"] in penalized_sids:
            issues.append(
                {
                    "sid": sig["sid"],
                    "block": sig["block"],
                    "field": sig["field"],
                    "start": sig["start"],
                    "end": sig["end"],
                    "kind": sig["kind"],
                    "category": sig["category"],
                    "word": sig["word"],
                    "text": sig["text"],
                    "why": sig["why"],
                    "detail": next(
                        (s["detail"] for s in sentences if s["sid"] == sig["sid"]), 0.0
                    ),
                }
            )
    # 文档级问题也放进 issues，但 sid 为空，重写环节会跳过
    for d in doclevel:
        sid = d.get("sid")
        sent = next((s for s in sentences if s["sid"] == sid), None) if sid else None
        issues.append(
            {
                "sid": sid,
                "block": sent["block"] if sent else None,
                "field": sent["field"] if sent else None,
                "start": sent["start"] if sent else None,
                "end": sent["end"] if sent else None,
                "kind": d["kind"],
                "category": d["category"],
                "word": d.get("word", ""),
                "text": d.get("text", ""),
                "why": d["why"],
                "detail": sent["detail"] if sent else 0.0,
            }
        )

    keep = []
    for sig in raw:
        if sig["sid"] in penalized_sids:
            continue
        sent = next((s for s in sentences if s["sid"] == sig["sid"]), None)
        reason = "单点信号，未成簇，属于正常写法"
        if sent and sent["quoted"]:
            reason = "在引号/引文内，是引用不是自述"
        elif sent and sent["detail"] >= 2.0:
            reason = f"该句细节密度 {sent['detail']}（≥2.0），是有血有肉的句子"
        keep.append({"sid": sig["sid"], "text": sig["text"], "word": sig["word"], "reason": reason})

    # 去重：同一句同一词只留一条
    seen = set()
    uniq = []
    for k in keep:
        key = (k["sid"], k["word"])
        if key not in seen:
            seen.add(key)
            uniq.append(k)

    return issues, uniq, clusters


def _positive(body: str, sentences: list[dict], scene: str | None) -> dict:
    base = 1.0 if scene == "anniversary" else 1.2
    text = re.sub(r"\s", "", body)
    density = detail_density(text)
    n = max(len(sentences), 1)
    first = sum(1 for s in sentences if re.search(r"我|咱", s["text"])) / n
    short = sum(1 for s in sentences if len(re.sub(r"\s", "", s["text"])) <= 12) / n

    def norm(v: float, b: float) -> float:
        return min(100.0, v / b * 100) if b else 0.0

    score = norm(density, base) * 0.5 + norm(first, 0.18) * 0.3 + norm(short, 0.22) * 0.2
    alarms = []
    if density < base:
        alarms.append(f"细节密度 {density} 低于基线 {base}：缺少数字、时间、地点、气味这类编不出来的东西")
    if first < 0.18:
        alarms.append(f"第一人称占比 {first:.0%} 偏低：读起来像旁观者，没有立场")
    if short < 0.22:
        alarms.append(f"短句占比 {short:.0%} 偏低：句子都太长，没有呼吸")
    return {
        "detail_density": density,
        "detail_baseline": base,
        "first_person": round(first, 3),
        "short_ratio": round(short, 3),
        "score": round(score, 1),
        "alarms": alarms,
    }


def _band(score: float) -> tuple[float, str]:
    for floor, name in BANDS:
        if score >= floor:
            return (floor, name)
    return (0, BANDS[-1][1])
