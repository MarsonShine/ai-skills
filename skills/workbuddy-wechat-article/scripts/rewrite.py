"""Apply single-sentence rewrites with hard verification.

The model only proposes a replacement for one sentence.  This module checks
that the rest of the block is untouched, the sentence count did not change,
facts such as numbers and quoted names survived, and the length stayed within
60–145% of the original.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import blocks
import voice

FACT_PATTERNS = [
    re.compile(r"\d+(?:\.\d+)?"),
    re.compile(r"[一二三四五六七八九十两半]+\s*(?:个|杯|次|岁|年|月|天|米|号|块|元|分钟|小时|页|本|张|件|套|斤|克|度|人|遍|趟)"),
    re.compile(r"\d{1,2}[:：]\d{2}|\d{4}年|\d{1,2}月\d{1,2}日|上周|昨天|前天|凌晨|早上|上午|中午|下午|傍晚|晚上|半夜"),
    re.compile(r"《[^》]{1,40}》|「[^」]{1,40}」|『[^』]{1,40}』|“[^”]{1,80}”"),
]

MIN_RATIO = 0.60
MAX_RATIO = 1.45


class RewriteError(ValueError):
    """Raised when a rewrite file or report is unusable."""


def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise RewriteError(f"无法读取文件：{error}") from error
    except json.JSONDecodeError as error:
        raise RewriteError(f"JSON 格式错误：第 {error.lineno} 行第 {error.colno} 列") from error


def facts(text: str) -> list[str]:
    found: list[str] = []
    for pattern in FACT_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            if value and value not in found:
                found.append(value)
    return found


def verify_sentence(old: str, new: str, issues: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    old = old.strip()
    new = new.strip()
    reasons: list[str] = []
    if not new:
        reasons.append("改写为空")
    if new == old:
        reasons.append("改写与原句相同")
    clean_new, _ = blocks.clean_with_map(new)
    if len(blocks.split_sentences(clean_new)) != 1:
        reasons.append("改写后不是一句话")
    old_len = max(1, blocks.content_length(old))
    new_len = blocks.content_length(new)
    ratio = new_len / old_len
    if not MIN_RATIO <= ratio <= MAX_RATIO:
        reasons.append(f"长度变化超出护栏（{ratio:.2f} 倍）")
    missing = [token for token in facts(old) if token not in new]
    if missing:
        reasons.append("丢失事实或专名：" + "、".join(missing[:5]))
    introduced = [word for word in voice.HARD_WORDS if word in new and word not in old]
    if introduced:
        reasons.append("新增硬性套话：" + "、".join(introduced[:3]))
    if any(word in old for word in voice.SOFT_WORDS) and new.count("——") > old.count("——") + 1:
        reasons.append("新增破折号")
    return {
        "ok": not reasons,
        "reasons": reasons,
        "ratio": round(ratio, 3),
        "facts": facts(old),
        "new_chars": new_len,
    }


def _rewrite_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        raw = raw.get("rewrites")
    if not isinstance(raw, list):
        raise RewriteError("rewrites 应为数组，或包含 rewrites 数组的对象")
    result = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise RewriteError(f"第 {index} 条改写应为对象")
        sentence_id = item.get("sentence_id")
        if not isinstance(sentence_id, str) or sentence_id.count(":") < 2:
            raise RewriteError(f"第 {index} 条改写缺少 sentence_id")
        if item.get("keep") is True:
            result.append({"sentence_id": sentence_id, "keep": True, "reason": str(item.get("reason", ""))})
            continue
        text = item.get("rewrite")
        if not isinstance(text, str):
            raise RewriteError(f"第 {index} 条改写缺少 rewrite 文本")
        result.append(
            {
                "sentence_id": sentence_id,
                "rewrite": text,
                "reason": str(item.get("reason", "")),
            }
        )
    return result


def _apply_one(document: dict[str, Any], sentence_id: str, new_text: str, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    parts = sentence_id.split(":", 2)
    try:
        block_index = int(parts[0])
        field = parts[1]
        index = int(parts[2])
    except (ValueError, IndexError) as error:
        raise RewriteError(f"sentence_id 无法解析：{sentence_id}") from error
    if block_index < 0 or block_index >= len(document["blocks"]):
        raise RewriteError(f"sentence_id 指向不存在的 block：{sentence_id}")
    block = document["blocks"][block_index]
    try:
        original_field = blocks.field_value(block, field)
    except (KeyError, IndexError, TypeError, blocks.DocumentError) as error:
        raise RewriteError(f"找不到字段 {sentence_id}") from error
    clean, mapping = blocks.clean_with_map(original_field)
    ranges = blocks.split_sentences(clean)
    if index >= len(ranges):
        raise RewriteError(f"找不到句子 {sentence_id}")
    start, end, old_clean = ranges[index]
    raw_start = mapping[start]
    raw_end = mapping[end - 1] + 1
    old_raw = original_field[raw_start:raw_end]
    check = verify_sentence(old_clean, new_text, issues)
    if not check["ok"]:
        return {"sentence_id": sentence_id, "old": old_raw, "new": new_text, "check": check, "rejected": True}
    updated = original_field[:raw_start] + new_text.strip() + original_field[raw_end:]
    blocks.set_field_value(block, field, updated)
    return {
        "sentence_id": sentence_id,
        "block_index": block_index,
        "field": field,
        "sentence_index": index,
        "old": old_raw,
        "new": new_text.strip(),
        "reason": "",
        "issues": issues,
        "check": check,
        "rejected": False,
    }


def apply(document: dict[str, Any], report: dict[str, Any], rewrites: Any) -> dict[str, Any]:
    """Apply verified rewrites and return a new document plus an audit trail."""
    if not isinstance(report, dict):
        raise RewriteError("诊断报告应为 JSON 对象")
    targets = {item["sentence_id"]: item for item in report.get("targets", [])}
    items = _rewrite_list(rewrites)

    def order(item: dict[str, Any]) -> tuple[int, str, int]:
        block_index, field, index = item["sentence_id"].split(":", 2)
        return int(block_index), field, int(index)

    # Apply later sentences first so earlier spans remain valid when several
    # rewrites land in the same block field.
    items.sort(key=order, reverse=True)
    seen: set[str] = set()
    candidate = copy.deepcopy(document)
    changes: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    applied_blocks: set[int] = set()

    for item in items:
        sentence_id = item["sentence_id"]
        if sentence_id in seen:
            rejected.append(
                {
                    "sentence_id": sentence_id,
                    "rejected": True,
                    "reasons": ["同一句重复提交，只应用第一条"],
                }
            )
            continue
        seen.add(sentence_id)
        target = targets.get(sentence_id)
        if target is None:
            rejected.append(
                {
                    "sentence_id": sentence_id,
                    "rejected": True,
                    "reasons": ["该句不在诊断器给出的可改写目标里"],
                }
            )
            continue
        if item.get("keep"):
            kept.append(
                {
                    "sentence_id": sentence_id,
                    "text": target["text"],
                    "reason": item.get("reason") or "模型判断本句无需改写",
                }
            )
            continue
        result = _apply_one(candidate, sentence_id, item["rewrite"], target.get("issues", []))
        if result is None or result.get("rejected"):
            rejected.append(result or {"sentence_id": sentence_id, "rejected": True, "reasons": ["未应用"]})
            continue
        result["reason"] = item.get("reason", "")
        result["change_reason"] = item.get("reason", "")
        changes.append(result)
        applied_blocks.add(result["block_index"])

    changes.sort(key=lambda item: (item["block_index"], item["field"], item["sentence_index"]))
    structure_ok = all(
        candidate["blocks"][index] == document["blocks"][index]
        for index in range(len(document["blocks"]))
        if index not in applied_blocks
    )
    changed = len(changes)
    return {
        "ok": True,
        "structure_ok": structure_ok,
        "document": candidate,
        "changes": changes,
        "rejected": rejected,
        "keep": kept,
        "applied": changed,
        "rejected_count": len(rejected),
        "block_count_changed": len(applied_blocks),
    }
