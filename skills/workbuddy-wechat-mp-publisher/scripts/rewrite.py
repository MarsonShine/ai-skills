"""定点重写：只改被诊断点中的那一句，其余逐字节不动。

为什么这么麻烦：
- 让模型「重写一段」几乎必然顺手改掉周围的句子，改完读者认不出是自己写的。
- 所以这里按字符 span 切片替换，一次只处理一句，并用四道校验兜底。
- 校验任一失败就丢弃改写，宁可留着毛边，也不接受「改坏了但看起来更顺」。
"""

from __future__ import annotations

import copy
import re

import voice

CHANGE_RATIO = (0.6, 1.45)   # 长度护栏
MAX_ROUNDS = 2


# ------------------------------------------------------------------ 字段读写
def get_field(block: dict, field: str):
    m = re.fullmatch(r"(\w+)\[(\d+)\]", field)
    if m:
        return block[m.group(1)][int(m.group(2))]
    return block.get(field)


def set_field(block: dict, field: str, value) -> None:
    m = re.fullmatch(r"(\w+)\[(\d+)\]", field)
    if m:
        block[m.group(1)][int(m.group(2))] = value
    else:
        block[field] = value


def splice(doc: dict, sid: str, new_text: str) -> dict:
    """按 sid 定位并替换，只动这一个 span。"""
    bi, field, si = sid.split(":")
    bi = int(bi)
    new = copy.deepcopy(doc)
    block = new["blocks"][bi]
    text = get_field(block, field)
    sents = voice.split_sentences(text)
    seg, st, en = sents[int(si)]
    set_field(block, field, text[:st] + new_text + text[en:])
    return new


# ------------------------------------------------------------------ 校验
def _facts(text: str) -> set[str]:
    """事实锚点：数字、时间、地名、英文专名。改写必须原样保留。"""
    out = set(voice.RE_NUM.findall(text))
    out |= {m for m in voice.RE_TIME.findall(text) if m}
    out |= set(voice.RE_PLACE.findall(text))
    out |= set(voice.RE_LATIN.findall(text))
    return {x for x in out if x not in voice.NUM_STOP}


def verify(orig_doc: dict, new_doc: dict, sid: str, old: str, new: str) -> tuple[bool, str]:
    """四道校验。返回 (通过?, 不通过原因)。

    顺序有讲究：先查「是不是还是一句」，再查结构。
    否则拆句会被 splice 切掉一半，反而报「改动了目标句之外的内容」，误导排查。
    """
    bi, field, si = sid.split(":")
    bi = int(bi)

    # 1. 句数不变：改写结果仍必须是一句
    n = len(voice.split_sentences(new))
    if n != 1:
        return False, f"改写后不是一句（{n} 句）"

    # 2. 事实不丢
    lost = _facts(old) - _facts(new)
    if lost:
        return False, f"丢失事实：{'、'.join(sorted(lost))}"

    # 3. 长度护栏
    ratio = len(new) / max(len(old), 1)
    if not (CHANGE_RATIO[0] <= ratio <= CHANGE_RATIO[1]):
        return False, f"长度变化 {ratio:.0%} 超出 {CHANGE_RATIO[0]:.0%}–{CHANGE_RATIO[1]:.0%}"

    # 4. 结构不变：把目标句还原后，整篇必须与原文逐字节一致
    reverted = copy.deepcopy(new_doc)
    block = reverted["blocks"][bi]
    text = get_field(block, field)
    sents = voice.split_sentences(text)
    if len(sents) <= int(si):
        return False, "还原时找不到原句"
    seg, st, en = sents[int(si)]
    set_field(block, field, text[:st] + old + text[en:])
    if reverted != orig_doc:
        return False, "改动了目标句之外的内容"

    return True, ""


# ------------------------------------------------------------------ 提示词
def build_prompt(profile: dict, target: str, issues: list[dict], prev: str, nxt: str) -> str:
    import profile as profile_mod

    kinds = sorted({i["kind"] for i in issues})
    detail = "\n".join(f"- {i['why']}" for i in issues)
    return f"""你在做一句话的局部改写，不是重写文章。

## 写作者的声音
{profile_mod.contract(profile)}

## 这一句的问题
原文：{target}
{detail}

## 上下文（只帮你理解语气，禁止修改，也不要出现在输出里）
前一句：{prev or "（无）"}
后一句：{nxt or "（无）"}

## 硬约束
1. 只输出改写后的一句话，不要解释、不要加引号、不要换行。
2. 不新增原文没有的事实，不补充场景细节。宁可不改，也不要编。
3. 数字、时间、地点、人名原样保留。
4. 长度与原文接近（0.6–1.45 倍）。
5. 仍然是一句话，不要拆成两句，不要加破折号。
6. 不要写成三个并列短语的排比。

## 允许不改
如果这句本身没问题，是在自然语境里的正常表达，直接输出：
{{"keep": true, "reason": "为什么这句不用改"}}
不要为了满足要求而硬改。问题类型：{",".join(kinds)}"""


def _parse_reply(raw: str) -> tuple[str | None, str]:
    """返回 (改写句, 拒绝理由)。改写句为 None 表示模型选择保留。"""
    text = (raw or "").strip()
    if not text:
        return None, "模型返回空"
    m = re.search(r'\{[^{}]*"keep"\s*:\s*true[^{}]*\}', text, re.S)
    if m:
        try:
            import json

            reason = json.loads(m.group(0)).get("reason", "模型认为无需修改")
        except Exception:
            reason = "模型认为无需修改"
        return None, reason
    # 去掉常见包裹
    text = re.sub(r"^```[a-z]*\n?|```$", "", text).strip()
    text = text.strip("\"“”'『』「」 ")
    text = text.split("\n")[0].strip()
    return (text or None), ""


# ------------------------------------------------------------------ 主流程
def run(
    doc: dict,
    profile: dict,
    complete,
    scene: str | None = None,
    max_rounds: int = MAX_ROUNDS,
) -> dict:
    """complete(prompt) -> str。返回改写后的 doc 与完整改动清单。"""
    work = copy.deepcopy(doc)
    before = voice.diagnose(work, profile, scene)
    changes: list[dict] = []
    frozen: dict[str, str] = {}   # sid -> 冻结原因

    current = before
    for rnd in range(1, max_rounds + 1):
        targets = _targets(current)
        if not targets:
            break
        progressed = False

        for item in targets:
            sid = item["sid"]
            if sid in frozen:
                continue
            bi, field, si = sid.split(":")
            text = get_field(work["blocks"][int(bi)], field)
            sents = voice.split_sentences(text)
            if len(sents) <= int(si):
                continue
            old, _, _ = sents[int(si)]
            sents_txt = [s[0] for s in sents]
            prev = sents_txt[int(si) - 1] if int(si) > 0 else ""
            nxt = sents_txt[int(si) + 1] if int(si) + 1 < len(sents_txt) else ""

            reply = complete(build_prompt(profile, old, item["issues"], prev, nxt))
            new, reason = _parse_reply(reply)
            if not new:
                frozen[sid] = reason or "模型选择保留"
                changes.append(
                    _change(sid, old, old, item["issues"], "kept", reason or "模型选择保留")
                )
                continue
            if new == old.strip():
                frozen[sid] = "改写与原句相同"
                changes.append(_change(sid, old, old, item["issues"], "kept", "改写与原句相同"))
                continue

            candidate = splice(work, sid, new)
            ok, why = verify(work, candidate, sid, old, new)
            if not ok:
                frozen[sid] = why
                changes.append(_change(sid, old, new, item["issues"], "rejected", why))
                continue

            work = candidate
            progressed = True
            changes.append(_change(sid, old, new, item["issues"], "applied", ""))

        after = voice.diagnose(work, profile, scene)
        gain = after["scores"]["final"] - current["scores"]["final"]
        current = after
        if not progressed:
            break
        if after["scores"]["final"] >= 85:
            break
        if gain < 2:
            break

    # 同一句二次仍命中同类问题 → 冻结，当作个人风格
    for sid in list(frozen):
        if frozen[sid] == "":
            frozen[sid] = "可能是个人风格"

    final_diag = voice.diagnose(work, profile, scene)
    return {
        "ok": True,
        "doc": work,
        "rounds": max_rounds,
        "before": before,
        "after": final_diag,
        "changes": changes,
        "summary": _summary(before, final_diag, changes),
    }


def _targets(diag: dict) -> list[dict]:
    """按 sid 归并句子级问题；文档级但没有 sid 的不进入重写。"""
    by_sid: dict[str, dict] = {}
    for i in diag.get("issues") or []:
        sid = i.get("sid")
        if not sid:
            continue
        entry = by_sid.setdefault(sid, {"sid": sid, "text": i.get("text") or "", "issues": []})
        entry["issues"].append(i)
    return list(by_sid.values())


def _change(sid: str, before: str, after: str, issues: list[dict], verdict: str, reason: str) -> dict:
    return {
        "sid": sid,
        "before": before,
        "after": after if verdict == "applied" else before,
        "proposed": after,
        "kinds": sorted({i["kind"] for i in issues}),
        "why": "；".join(sorted({i["why"] for i in issues})),
        "verdict": verdict,
        "reason": reason,
    }


def _summary(before: dict, after: dict, changes: list[dict]) -> dict:
    applied = [c for c in changes if c["verdict"] == "applied"]
    rejected = [c for c in changes if c["verdict"] == "rejected"]
    kept = [c for c in changes if c["verdict"] == "kept"]
    need = [
        a for a in (after.get("positive") or {}).get("alarms", [])
    ]
    return {
        "score_before": before["scores"]["final"],
        "score_after": after["scores"]["final"],
        "band_before": before["scores"]["band"],
        "band_after": after["scores"]["band"],
        "applied": len(applied),
        "rejected": len(rejected),
        "kept": len(kept),
        "need_your_detail": need,
        "note": (
            "改写只动被点中的句子，其余原文未变。"
            "被拒绝的改写说明模型试图加事实或改坏结构，已丢弃。"
        ),
    }
