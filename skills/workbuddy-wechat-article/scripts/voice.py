"""Deterministic AI-flavour detector for personal WeChat articles.

The detector is intentionally rule-based: the same blocks and profile always
produce the same report.  It never calls a model.  A rewrite step may follow,
but only for the sentences this report marks as penalised.
"""

from __future__ import annotations

import re
import statistics
from typing import Any, Iterable

import blocks

HARD_WORDS = [
    "赋能", "闭环", "抓手", "底层逻辑", "颗粒度", "组合拳", "护城河",
    "顶层设计", "降本增效", "颠覆式", "沉浸式", "全链路", "生态位",
]

SOFT_WORDS = [
    "首先", "其次", "最后", "综上", "总而言之", "不难发现", "值得注意的是",
    "众所周知", "显而易见", "某种程度上", "一定程度上", "某种意义上",
    "不得不说", "在这个时代",
]

ENDING_CLICHES = [
    "未来可期", "值得期待", "充满希望", "越来越好", "明天会更好", "无限可能",
    "共勉", "愿你我", "一切都会好", "新的开始", "继续前行", "加油",
]
ENDING_PATTERNS = [
    re.compile(r"(希望|愿).{0,20}(都能|可以|会)"),
    re.compile(r"这就是.{0,10}的意义。?"),
]

NEG_PATTERNS = [
    re.compile(r"不是[^。！？\n]{1,36}(?:，|,)?\s*(?:而是|就是|乃是|才是)"),
    re.compile(r"(?:不只是|不仅是|不止是|不光)[^。！？\n]{1,36}(?:，|,)?\s*(?:更是|还是|而且)"),
    re.compile(r"并非[^。！？\n]{1,36}(?:，|,)?\s*而是"),
    re.compile(r"not\s+(?:just|only|merely)[^.!?]{1,60}but", re.IGNORECASE),
]

TRIPLE_PATTERNS = [
    re.compile(r"既[^。！？\n]{1,20}又[^。！？\n]{1,20}还"),
    re.compile(r"不仅[^。！？\n]{1,20}还[^。！？\n]{1,20}更"),
    re.compile(r"一[^。！？\n、，]{1,12}二[^。！？\n、，]{1,12}三"),
]

ACTION_VERBS = (
    "拿 放 走 跑 坐 站 煮 冲 喝 拍 写 笑 哭 抱 推 按 拧 翻 拎 洗 擦 切 炒 盛 递 "
    "拉 关 开 穿 脱 躺 蹲 爬 追 捡 挂 收 晒 折 咬 嚼 咽 摸 闻 听 看 数 等 挤 背 "
    "牵 扶 踩 踢 敲 拆 装 修 浇 喂 哄 叫 喊 问 答 读 画 剪 贴 缝 扫 拖 泡 蒸 烤 "
    "煎 炖 熬 醒 睡 起 回 进 出 上 下 转 停 掉 摔 碰 撞 躲 藏 接 抢 换 找 忘 记 "
    "想 猜 试 学 教 带 送 陪 挤 搬 抬 挖 种 收 晾 叠 铺 关 锁 拧 塞 掏 掏 挽 甩"
).split()

SENSE_WORDS = (
    "咕嘟 沙沙 啪 烫 凉 酸 软 硬 湿 干 香 苦 甜 咸 辣 涩 滑 糙 暖 冷 闷 亮 暗 "
    "吵 静 沉 轻 重 痒 疼 麻 油 腻 清 脆 黏 稠 稀 焦 糊 腥 膻"
).split()

TIME_PATTERN = re.compile(
    r"\d{1,2}[:：]\d{2}|\d{4}年|\d{1,2}月\d{1,2}日|上周|昨天|前天|凌晨|早上|上午|中午|下午|傍晚|晚上|半夜"
)
NUMBER_MEASURE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:个|杯|次|点|岁|年|月|日|天|米|公里|号|块|元|分钟|小时|页|本|张|件|套|斤|克|度|人|遍|趟|只|条|颗|粒|片|碗|盘|袋|瓶|罐|盒)"
)
CHINESE_NUMBER_MEASURE = re.compile(r"[一二三四五六七八九十两半]+\s*(?:个|杯|次|岁|年|月|天|米|号|块|元|分钟|小时|页|本|张|件|套|斤|克|度|人|遍|趟)")
PROPER_PATTERN = re.compile(
    r"《[^》]{1,30}》|「[^」]{1,30}」|[\u4e00-\u9fff]{2,4}(?:市|区|街|路|店|公园|学校|医院|幼儿园)|[A-Z][A-Za-z]{2,}"
)
PARAGRAPH_BAND = 20
SHORT_SENTENCE = 12
MIN_CHARS_FOR_RHYTHM = 200

CATEGORY_CAPS = {
    "lexicon": 25,
    "rhythm": 20,
    "rhetoric": 20,
    "paragraph": 15,
    "ending": 10,
}
SEVERITY_POINTS = {1: 3, 2: 6, 3: 9}

BANDS = ("机器味重", "明显AI味", "可用，少量机器味", "人味足")


def _signal(
    code: str,
    category: str,
    severity: int,
    unit: blocks.Unit,
    sentence: blocks.Sentence | None,
    evidence: str,
    message: str,
    exempt: str | None = None,
) -> dict[str, Any]:
    sentence = sentence or (unit.sentences[0] if unit.sentences else None)
    if sentence and _detail_density(sentence.text) >= 2.0:
        severity = max(1, severity - 1)
    return {
        "code": code,
        "category": category,
        "severity": severity,
        "level": "hard" if severity >= 2 else "soft",
        "block_index": unit.block_index,
        "field": unit.field,
        "sentence_index": sentence.index if sentence else 0,
        "sentence_id": sentence.sentence_id if sentence else "",
        "span": [sentence.start, sentence.end] if sentence else [0, 0],
        "sentence_text": sentence.text if sentence else "",
        "evidence": evidence[:120],
        "message": message,
        "exempt_reason": exempt,
    }


def _word_hits(text: str, word: str) -> Iterable[int]:
    start = 0
    while True:
        found = text.find(word, start)
        if found < 0:
            return
        yield found
        start = found + max(1, len(word))


def _sentence_at(unit: blocks.Unit, raw_start: int) -> blocks.Sentence | None:
    for sentence in unit.sentences:
        if sentence.start <= raw_start < sentence.end:
            return sentence
    if not unit.sentences:
        return None
    return min(unit.sentences, key=lambda sentence: abs(sentence.start - raw_start))


def _detail_score(text: str) -> tuple[float, int]:
    """Weighted concrete-detail count and character count (per 100 chars)."""
    score = 0.0
    score += 1.0 * len(NUMBER_MEASURE.findall(text))
    score += 1.0 * len(CHINESE_NUMBER_MEASURE.findall(text))
    score += 1.0 * len(TIME_PATTERN.findall(text))
    score += 1.2 * len(PROPER_PATTERN.findall(text))
    score += 0.6 * sum(text.count(verb) for verb in ACTION_VERBS)
    score += 0.8 * sum(text.count(word) for word in SENSE_WORDS)
    return score, blocks.content_length(text)


def _detail_density(text: str) -> float:
    score, length = _detail_score(text)
    return score / (length / 100) if length else 0.0


def _lexicon(units: list[blocks.Unit], profile: dict[str, Any] | None) -> tuple[list[dict[str, Any]], float]:
    hard = list(HARD_WORDS)
    soft = list(SOFT_WORDS)
    whitelist: list[str] = []
    if profile:
        hard.extend(profile.get("taboo", {}).get("hard_words", []))
        soft.extend(profile.get("taboo", {}).get("soft_words", []))
        whitelist = profile.get("topics", {}).get("frequent", []) + profile.get("topics", {}).get("series", [])
    hard = list(dict.fromkeys(hard))
    soft = list(dict.fromkeys(soft))
    signals: list[dict[str, Any]] = []
    soft_hits = 0
    total_chars = sum(blocks.content_length(unit.text) for unit in units)
    for unit in units:
        clean, mapping = blocks.clean_with_map(unit.text)
        quote_ranges = blocks.quoted_ranges(clean)
        for word, severity in [(word, 2) for word in hard] + [(word, 1) for word in soft]:
            for position in _word_hits(clean, word):
                end = position + len(word)
                sentence = _sentence_at(unit, mapping[position])
                exempt = None
                if unit.quoted or unit.block_type in {"quote", "list", "callout", "code"}:
                    exempt = "引用、列表或提示块内，不计入行文套话"
                elif blocks.inside(quote_ranges, position, end):
                    exempt = "位于引号或书名号内，属于引用"
                elif any(word in topic for topic in whitelist):
                    exempt = "属于作者常用主题词汇，不判为套话"
                signal = _signal(
                    "hard_word" if severity == 2 else "soft_word",
                    "lexicon",
                    severity,
                    unit,
                    sentence,
                    word,
                    "硬性套话词" if severity == 2 else "慎用套话词",
                    exempt,
                )
                signal["span"] = [mapping[position], mapping[end - 1] + 1]
                signals.append(signal)
                if severity == 1:
                    soft_hits += 1
    if total_chars and soft_hits / (total_chars / 1000) > 2:
        first = next((unit for unit in units if unit.sentences), None)
        if first:
            signals.append(
                _signal(
                    "soft_dense", "lexicon", 1, first, first.sentences[0],
                    f"{soft_hits} 次", "慎用词密度偏高",
                )
            )
    return signals, total_chars


def _body_sentences(units: list[blocks.Unit]) -> list[blocks.Sentence]:
    return [
        sentence
        for unit in units
        if unit.block_type not in {"h2", "h3", "quote"} and not unit.quoted
        for sentence in unit.sentences
    ]


def _rhythm(units: list[blocks.Unit], total_chars: int) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    sentences = _body_sentences(units)
    lengths = [blocks.content_length(sentence.text) for sentence in sentences]
    positives: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    stats: dict[str, Any] = {"n": len(lengths), "mean": 0.0, "stdev": 0.0, "cv": 0.0, "short_ratio": 0.0}
    if not lengths:
        return signals, stats, positives
    mean = statistics.fmean(lengths)
    stdev = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    cv = stdev / mean if mean else 0.0
    short_ratio = sum(1 for value in lengths if value <= SHORT_SENTENCE) / len(lengths)
    stats = {
        "n": len(lengths),
        "mean": round(mean, 2),
        "stdev": round(stdev, 2),
        "cv": round(cv, 3),
        "short_ratio": round(short_ratio, 3),
        "min": min(lengths),
        "max": max(lengths),
    }
    if total_chars >= MIN_CHARS_FOR_RHYTHM and len(lengths) >= 8 and cv < 0.32:
        signal = _signal(
            "rhythm_uniform", "rhythm", 2, _unit_of(sentences[0], units), sentences[0],
            f"CV={cv:.2f}", "句长过于均匀，缺少呼吸起伏",
        )
        signal["meta"] = {"cv": round(cv, 3), "mean": round(mean, 2)}
        signals.append(signal)
    run_start = 0
    while run_start <= len(lengths) - 4:
        window = lengths[run_start:run_start + 4]
        if max(window) - min(window) <= 3:
            first = sentences[run_start]
            unit = _unit_of(first, units)
            signal = _signal(
                "flat_run", "rhythm", 1, unit, first,
                "–".join(str(value) for value in window),
                f"连续四句长度接近（第 {run_start + 1}–{run_start + 4} 句）",
            )
            signal["run"] = [run_start, run_start + 3]
            signal["meta"] = {
                "run_span": [run_start, run_start + 3],
                "sentence_indexes": list(range(run_start, run_start + 4)),
                "lengths": window,
            }
            signals.append(signal)
            run_start += 4
        else:
            run_start += 1
    if total_chars >= MIN_CHARS_FOR_RHYTHM and len(lengths) >= 10 and min(lengths) > SHORT_SENTENCE:
        positives.append(
            {
                "code": "no_short_sentence",
                "value": min(lengths),
                "baseline": SHORT_SENTENCE,
                "level": "warn",
                "message": "整篇没有短句，读起来缺少停顿",
            }
        )
    return signals, stats, positives


def _unit_of(sentence: blocks.Sentence, units: list[blocks.Unit]) -> blocks.Unit:
    for unit in units:
        if unit.block_index == sentence.block_index and unit.field == sentence.field:
            return unit
    return units[0]


def _dash_runs(text: str) -> int:
    count = 0
    for match in re.finditer(r"—+", text):
        run = match.group(0)
        if len(run) >= 2:
            count += 1
        else:
            before = text[match.start() - 1] if match.start() else ""
            after = text[match.end()] if match.end() < len(text) else ""
            if not (before.isdigit() and after.isdigit()):
                count += 1
    return count


def _triple_hit(text: str) -> str | None:
    clauses = [clause.strip() for clause in re.split(r"[、，]", text) if len(clause.strip()) >= 2]
    for index in range(len(clauses) - 2):
        trio = clauses[index:index + 3]
        if any(blocks.DIGIT.search(clause) for clause in trio):
            continue
        lengths = [blocks.content_length(clause) for clause in trio]
        if not all(2 <= value <= 10 for value in lengths):
            continue
        if max(lengths) - min(lengths) > 2:
            continue
        shared = False
        for left in range(3):
            for right in range(left + 1, 3):
                a, b = trio[left], trio[right]
                if a[0] == b[0] or a[-1] == b[-1]:
                    shared = True
                elif len(a) >= 2 and len(b) >= 2 and (a[:2] == b[:2] or a[-2:] == b[-2:]):
                    shared = True
        if shared:
            return "、".join(trio)
    for pattern in TRIPLE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def _rhetoric(units: list[blocks.Unit], total_chars: int) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    dash_total = 0
    for unit in units:
        dash_total += _dash_runs(unit.text)
    dash_density = dash_total / (total_chars / 100) if total_chars else 0.0

    neg_total = 0
    triple_total = 0
    for unit in units:
        if unit.quoted or unit.block_type in {"quote", "code"}:
            continue
        for sentence in unit.sentences:
            text = sentence.text
            dash_count = _dash_runs(text)
            if dash_count and (dash_total >= 3 or dash_density > 0.33 or dash_count >= 2):
                signal = _signal(
                    "em_dash", "rhetoric", 2, unit, sentence,
                    "—" * max(2, dash_count), "破折号密集，像解释性插入语",
                )
                signal["dash_count"] = dash_count
                signal["meta"] = {"dash_count": dash_count}
                signals.append(signal)
            elif dash_count:
                signals.append(
                    _signal(
                        "em_dash", "rhetoric", 1, unit, sentence,
                        "—", "单次破折号，可能是作者固定语感",
                        "单次出现，未形成密度",
                    )
                )
            for pattern in NEG_PATTERNS:
                for match in pattern.finditer(text):
                    neg_total += 1
                    signals.append(
                        _signal(
                            "neg_parallel", "rhetoric", 2, unit, sentence,
                            match.group(0)[:40], "否定式排比：不是……而是……",
                        )
                    )
            if unit.block_type not in {"list", "callout"} and not re.match(r"^(比如|例如|如：)", text):
                triple = _triple_hit(text)
                if triple:
                    triple_total += 1
                    signals.append(
                        _signal(
                            "triple_parallel", "rhetoric", 2, unit, sentence,
                            triple[:60], "三连排比，句式过于整齐",
                        )
                    )
    # A single rhetorical device is not evidence of machine writing.  Keep it,
    # but remember it so the report can explain why it was not penalised.
    for signal in signals:
        if signal["code"] == "neg_parallel" and neg_total == 1:
            signal["exempt_reason"] = "全文仅一次否定式排比，可能是作者固定语感"
            signal["severity"] = 1
            signal["level"] = "soft"
        if signal["code"] == "triple_parallel" and triple_total == 1:
            signal["exempt_reason"] = "全文仅一次三连排比，可能是列举"
            signal["severity"] = 1
            signal["level"] = "soft"
    return signals


def _paragraphs(units: list[blocks.Unit]) -> tuple[list[dict[str, Any]], list[int]]:
    paragraphs = [
        (unit, len(blocks.clean_with_map(unit.text)[0]))
        for unit in units
        if unit.block_type in {"p", "lead"}
    ]
    lengths = [length for _, length in paragraphs]
    if len(lengths) < 4:
        return [], lengths
    mean = statistics.fmean(lengths)
    ratio = (max(lengths) - min(lengths)) / mean if mean else 0.0
    signals: list[dict[str, Any]] = []
    severity = 0
    if ratio < 0.22:
        severity = 1
    if len(lengths) >= 5:
        low = min(lengths)
        in_band = sum(1 for length in lengths if low <= length < low + PARAGRAPH_BAND)
        if in_band / len(lengths) >= 0.8:
            severity = 2
    if severity:
        unit = paragraphs[0][0]
        sentence = unit.sentences[0] if unit.sentences else None
        signal = _signal(
            "para_uniform", "paragraph", severity, unit, sentence,
            f"{min(lengths)}–{max(lengths)} 字",
            "段落长度过于整齐，像按模板分段",
        )
        signal["meta"] = {
            "lengths": lengths,
            "range_ratio": round(ratio, 3),
            "block_indexes": [unit.block_index for unit, _ in paragraphs],
        }
        signals.append(signal)
    weak = False
    if len(lengths) >= 4 and not severity:
        for start in range(len(lengths) - 3):
            window = lengths[start:start + 4]
            if max(window) - min(window) <= 0.12 * mean:
                weak = True
                unit = paragraphs[start][0]
                sentence = unit.sentences[0] if unit.sentences else None
                signals.append(
                    _signal(
                        "para_run", "paragraph", 1, unit, sentence,
                        "–".join(str(value) for value in window),
                        f"连续四段长度接近（第 {start + 1}–{start + 4} 段）",
                    )
                )
                break
    return signals, lengths


def _ending(units: list[blocks.Unit], scene: str) -> list[dict[str, Any]]:
    prose = [unit for unit in units if unit.block_type in {"p", "lead", "footer"}]
    if not prose:
        return []
    tail = prose[-2:]
    signals: list[dict[str, Any]] = []
    for unit in tail:
        text = unit.text
        hits: list[tuple[int, int, str]] = []
        for word in ENDING_CLICHES:
            start = text.find(word)
            if start >= 0:
                hits.append((start, start + len(word), word))
        for pattern in ENDING_PATTERNS:
            match = pattern.search(text)
            if match:
                hits.append((match.start(), match.end(), match.group(0)))
        if not hits:
            continue
        total, chars = _detail_score(text)
        if chars and total / (chars / 100) > 0:
            continue
        sentence = unit.sentences[-1] if unit.sentences else None
        evidence = hits[0][2]
        exempt = None
        if scene == "anniversary" and ("祝" in text or "祝福" in text):
            exempt = "纪念日祝福是合理文体"
        signal = _signal(
            "empty_ending", "ending", 2, unit, sentence, evidence,
            "结尾落在泛化祝福上，没有具体的人或事",
            exempt,
        )
        if sentence:
            signal["span"] = [sentence.start, sentence.end]
        signals.append(signal)
    return signals


def _positive(
    units: list[blocks.Unit],
    lengths: list[int],
    rhythm_stats: dict[str, Any],
    scene: str,
) -> list[dict[str, Any]]:
    text = "\n".join(unit.text for unit in units if not unit.quoted)
    chars = blocks.content_length(text)
    detail = _detail_density(text)
    sentences = _body_sentences(units)
    first_person = sum(
        1 for sentence in sentences if any(word in sentence.text for word in ("我", "我们", "咱", "俺"))
    )
    first_ratio = first_person / len(sentences) if sentences else 0.0
    short_ratio = rhythm_stats.get("short_ratio", 0.0)
    cv = rhythm_stats.get("cv", 0.0)
    sensory = sum(text.count(word) for word in SENSE_WORDS)
    sensory_per100 = sensory / (chars / 100) if chars else 0.0
    baseline = 1.0 if scene == "anniversary" else 1.2
    result = [
        {
            "code": "detail_density",
            "value": round(detail, 2),
            "baseline": baseline,
            "level": "ok" if detail >= baseline else "warn",
            "message": "具体细节够" if detail >= baseline else "具体细节偏少，多写一个动作或一个数字",
        },
        {
            "code": "first_person_ratio",
            "value": round(first_ratio, 2),
            "baseline": 0.12 if scene == "anniversary" else 0.18,
            "level": "ok" if first_ratio >= (0.12 if scene == "anniversary" else 0.18) else "warn",
            "message": "第一人称在场" if first_ratio >= (0.12 if scene == "anniversary" else 0.18) else "“我”退得太远，读起来像旁观稿",
        },
        {
            "code": "short_sentence_ratio",
            "value": round(short_ratio, 2),
            "baseline": 0.22,
            "level": "ok" if short_ratio >= 0.22 else "warn",
            "message": "有短句呼吸" if short_ratio >= 0.22 else "缺少短句呼吸",
        },
        {
            "code": "sentence_cv",
            "value": round(cv, 2),
            "baseline": 0.35,
            "level": "ok" if cv >= 0.35 else "warn",
            "message": "句长有落差" if cv >= 0.35 else "句长落差不足",
        },
        {
            "code": "sensory_per100",
            "value": round(sensory_per100, 2),
            "baseline": 0.5,
            "level": "ok" if sensory_per100 >= 0.5 else "warn",
            "message": "有可感的细节" if sensory_per100 >= 0.5 else "缺少可感的细节（声音、温度、气味）",
        },
    ]
    return result


def _cluster(
    signals: list[dict[str, Any]],
    total_chars: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active = [signal for signal in signals if not signal.get("exempt_reason")]
    if not active:
        return [], signals
    active.sort(key=lambda item: (item["block_index"], item["sentence_index"], item["span"][0]))
    clusters: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    last_block = -10
    for signal in active:
        if current and signal["block_index"] > last_block + 1:
            clusters.append({"id": f"c{len(clusters) + 1}", "signals": current})
            current = []
        current.append(signal)
        last_block = signal["block_index"]
    if current:
        clusters.append({"id": f"c{len(clusters) + 1}", "signals": current})

    dash_total = sum(
        signal.get("dash_count", 1)
        for signal in signals
        if signal["code"] == "em_dash" and not signal.get("exempt_reason")
    )
    for cluster in clusters:
        members = cluster["signals"]
        categories = {signal["category"] for signal in members}
        counts: dict[str, int] = {}
        for signal in members:
            counts[signal["category"]] = counts.get(signal["category"], 0) + 1
        strong = False
        if sum(1 for signal in members if signal["code"] == "hard_word") >= 2:
            strong = True
        if counts.get("rhetoric", 0) >= 2 and any(
            signal["code"] in {"neg_parallel", "triple_parallel"} for signal in members
        ):
            strong = True
        if any(signal["code"] == "em_dash" for signal in members) and dash_total >= 3:
            strong = True
        cluster["categories"] = sorted(categories)
        cluster["penalized"] = (len(members) >= 3 and len(categories) >= 2) or strong
        cluster["signal_count"] = len(members)

    if not any(cluster["penalized"] for cluster in clusters):
        categories = {signal["category"] for signal in active}
        if len(categories) >= 3 and len(active) >= 5:
            global_cluster = {
                "id": "global",
                "signals": active,
                "categories": sorted(categories),
                "signal_count": len(active),
                "penalized": True,
                "global": True,
            }
            for cluster in clusters:
                cluster["penalized"] = False
            clusters.append(global_cluster)
            for signal in active:
                signal["severity"] = min(signal["severity"], 1)
                signal["level"] = "soft"

    for cluster in clusters:
        for signal in cluster["signals"]:
            signal["cluster_id"] = cluster["id"]
            signal["penalized"] = cluster["penalized"]
    return clusters, signals


def _keep_reason(signal: dict[str, Any], unit: blocks.Unit) -> str:
    if signal.get("exempt_reason"):
        return signal["exempt_reason"]
    if signal["code"] in {"em_dash", "neg_parallel", "triple_parallel"}:
        return "单点信号，未与相邻段落形成簇，可能是作者语感"
    if unit.block_type in {"list", "callout", "checklist"}:
        return "信息块里的短句，不是行文套话"
    detail = _detail_density(signal.get("sentence_text", ""))
    if detail >= 2.0:
        return "句子细节密度高，像具体观察，不扣分"
    return "单点信号，未形成跨类别簇"


def analyze(
    document: dict[str, Any],
    profile: dict[str, Any] | None = None,
    scene: str | None = None,
) -> dict[str, Any]:
    blocks_list = document["blocks"]
    units = blocks.iter_units(blocks_list)
    scene = scene or document.get("scene") or (profile or {}).get("typesetting", {}).get("scene") or "daily"
    if scene == "auto":
        scene = "daily"
    signals: list[dict[str, Any]] = []

    lexicon, total_chars = _lexicon(units, profile)
    signals.extend(lexicon)
    rhythm, rhythm_stats, rhythm_positive = _rhythm(units, total_chars)
    if total_chars >= MIN_CHARS_FOR_RHYTHM:
        signals.extend(rhythm)
    else:
        rhythm = []
    signals.extend(_rhetoric(units, total_chars))
    paragraph, paragraph_lengths = _paragraphs(units)
    if total_chars < MIN_CHARS_FOR_RHYTHM:
        paragraph = []
    signals.extend(paragraph)
    signals.extend(_ending(units, scene))

    clusters, signals = _cluster(signals, total_chars)

    deductions: dict[str, int] = {}
    for signal in signals:
        if not signal.get("penalized"):
            continue
        points = SEVERITY_POINTS[min(3, max(1, signal["severity"]))]
        deductions[signal["category"]] = deductions.get(signal["category"], 0) + points
    category_deductions = {category: min(cap, deductions.get(category, 0)) for category, cap in CATEGORY_CAPS.items()}
    total_deduction = sum(category_deductions.values())
    ai_score = max(10, min(100, 100 - total_deduction))

    positives = _positive(units, paragraph_lengths, rhythm_stats, scene) + rhythm_positive
    detail = next(item["value"] for item in positives if item["code"] == "detail_density")
    first_person = next(item["value"] for item in positives if item["code"] == "first_person_ratio")
    short_ratio = rhythm_stats.get("short_ratio", 0.0)
    cv = rhythm_stats.get("cv", 0.0)
    sensory = next(item["value"] for item in positives if item["code"] == "sensory_per100")
    human_score = round(
        35 * min(1.0, detail / 2.0)
        + 20 * min(1.0, first_person / 0.30)
        + 20 * min(1.0, short_ratio / 0.35)
        + 15 * min(1.0, cv / 0.55)
        + 10 * min(1.0, sensory / 1.5)
    )
    final = round(0.6 * ai_score + 0.4 * human_score)
    index = 0
    for candidate, threshold in enumerate((85, 70, 55)):
        if final >= threshold:
            index = 3 - candidate
            break
    gate = "human_ok"
    if human_score < 40 and index > 0:
        index -= 1
        gate = "human_low_downgraded"
    band = BANDS[index]

    # Stable, explainable output.
    signals.sort(key=lambda item: (item["block_index"], item["field"], item["sentence_index"], item["span"][0], item["code"]))
    issues = []
    keep = []
    for number, signal in enumerate(signals, start=1):
        issue = {
            "id": f"i{number}",
            "code": signal["code"],
            "category": signal["category"],
            "level": signal["level"],
            "severity": signal["severity"],
            "penalized": bool(signal.get("penalized")),
            "block_index": signal["block_index"],
            "field": signal["field"],
            "sentence_index": signal["sentence_index"],
            "span": signal["span"],
            "sentence_id": signal["sentence_id"],
            "sentence_text": signal["sentence_text"],
            "evidence": signal["evidence"],
            "message": signal["message"],
            "cluster_id": signal.get("cluster_id"),
        }
        issues.append(issue)
        if signal.get("meta"):
            issue.update(signal["meta"])
        if not signal.get("penalized"):
            unit = _unit_of(
                blocks.Sentence(
                    signal["block_index"], signal["field"], signal["sentence_index"],
                    signal["sentence_text"], signal["span"][0], signal["span"][1], False,
                ),
                units,
            ) if units else units[0]
            keep.append(
                {
                    "code": signal["code"],
                    "block_index": signal["block_index"],
                    "field": signal["field"],
                    "sentence_index": signal["sentence_index"],
                    "span": signal["span"],
                    "sentence_id": signal["sentence_id"],
                    "text": signal["sentence_text"],
                    "reason": _keep_reason(signal, unit) if units else "单点信号",
                }
            )

    cluster_output = [
        {
            "id": cluster["id"],
            "categories": cluster["categories"],
            "signals": cluster["signal_count"],
            "penalized": cluster["penalized"],
            "deduction": sum(
                SEVERITY_POINTS[min(3, max(1, signal["severity"]))]
                for signal in cluster["signals"]
                if signal.get("penalized")
            ),
        }
        for cluster in clusters
    ]

    targets = _targets(units, signals)
    sentence_count = len(blocks.sentences_of(units))
    paragraph_count = len([unit for unit in units if unit.block_type in {"p", "lead"}])
    return {
        "meta": {
            "chars": total_chars,
            "sentences": sentence_count,
            "paragraphs": paragraph_count,
            "scene": scene,
            "profile": (profile or {}).get("identity", {}).get("name", ""),
        },
        "scores": {
            "final": final,
            "ai": ai_score,
            "human": human_score,
            "band": band,
            "gate": gate,
            "deductions": category_deductions,
        },
        "issues": issues,
        "clusters": cluster_output,
        "keep": keep,
        "positive": positives,
        "targets": targets,
    }


def _targets(units: list[blocks.Unit], signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sentences = {sentence.sentence_id: sentence for sentence in blocks.sentences_of(units)}
    sentence_codes = {
        "hard_word", "soft_word", "em_dash", "neg_parallel", "triple_parallel", "empty_ending",
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for signal in signals:
        if signal.get("penalized") and signal["sentence_id"] and signal["code"] in sentence_codes:
            grouped.setdefault(signal["sentence_id"], []).append(signal)
    result = []
    for sentence_id, items in grouped.items():
        sentence = sentences.get(sentence_id)
        if sentence is None:
            continue
        ordered = [
            candidate
            for candidate in blocks.sentences_of(units)
            if candidate.block_index == sentence.block_index and candidate.field == sentence.field
        ]
        before = ""
        after = ""
        for index, candidate in enumerate(ordered):
            if candidate.sentence_id == sentence_id:
                before = ordered[index - 1].text if index else ""
                after = ordered[index + 1].text if index + 1 < len(ordered) else ""
                break
        result.append(
            {
                "sentence_id": sentence_id,
                "block_index": sentence.block_index,
                "field": sentence.field,
                "sentence_index": sentence.index,
                "text": sentence.text,
                "before": before,
                "after": after,
                "issues": [
                    {
                        "code": item["code"],
                        "severity": item["severity"],
                        "evidence": item["evidence"],
                        "message": item["message"],
                    }
                    for item in items
                ],
            }
        )
    result.sort(key=lambda item: (item["block_index"], item["field"], item["sentence_index"]))
    return result


def analyze_text(text: str, profile: dict[str, Any] | None = None, scene: str | None = None) -> dict[str, Any]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    document = {"blocks": [{"type": "p", "text": part} for part in paragraphs], "scene": scene or "daily"}
    return analyze(document, profile, scene)
