"""LLM 适配层：粗文案 → 结构化 blocks，以及标题/摘要。

两种模式：
- 有 API key：让模型按人格把文案拆成 blocks，只允许用白名单里的块型。
- 没 key：走确定性降级（分段 + 均匀插图 + 场景块兜底），保证全流程能跑通。

无论哪种模式，**事实都来自用户原文**。模型只做分节、配图、起标题，
没让它编细节；需要细节时留给用户补（见 rewrite 的 need_your_detail）。
"""

from __future__ import annotations

import json
import os
import re

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

import profile as profile_mod

COMMON_BLOCKS = [
    "h2", "h3", "lead", "p", "quote", "list", "callout",
    "image", "images", "divider", "footer",
]
SCENE_BLOCKS = {
    "family": ["photo_polaroid", "kid_quote", "checklist", "dialogue"],
    "travel": ["timeline", "route_table", "weather_card", "stamp"],
    "daily": ["drop_cap", "margin_note", "letter_paper", "sign_off"],
    "anniversary": ["countdown_card", "ticket_stub", "compare_pair", "memory_band"],
}

TITLE_MAX = 32    # 微信标题上限，超了 draft/add 会报 40008
DIGEST_MAX = 120  # 摘要上限


def config() -> dict:
    return {
        "base": (os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
        "key": os.environ.get("LLM_API_KEY") or "",
        "model": os.environ.get("LLM_MODEL") or "gpt-4o-mini",
    }


def available() -> bool:
    return bool(config()["key"]) and requests is not None


# ------------------------------------------------------------------ 调用
def complete(prompt: str, system: str | None = None, temperature: float = 0.3,
             max_tokens: int = 1200, timeout: int = 60) -> str:
    cfg = config()
    if not cfg["key"]:
        raise RuntimeError("未配置 LLM_API_KEY")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    r = requests.post(
        f"{cfg['base']}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
        json={
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"LLM {r.status_code}: {r.text[:300]}")
    data = r.json()
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")


def _extract_json(text: str):
    text = re.sub(r"^```[a-z]*\n?|```$", "", (text or "").strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"[\[{].*[\]}]", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


# ------------------------------------------------------------------ 生成
def expand(raw_text: str, images: list[str], profile: dict | None = None,
           scene: str | None = None, rewrite: bool = False) -> dict:
    """返回 {blocks, title, digest, warnings, source}。source 为 llm / heuristic。"""
    profile = profile or {}
    scene = _scene(scene or (profile.get("typesetting") or {}).get("scene"), raw_text)
    warnings: list[str] = []

    if rewrite and available():
        try:
            out = _expand_llm(raw_text, images, profile, scene)
            out["warnings"] += warnings
            return out
        except Exception as e:  # 网络/解析失败都降级，别让整条链断在文案上
            warnings.append(f"模型改写失败，已退回保真模式：{e}")

    blocks = heuristic(raw_text, images, scene)
    return {
        "blocks": blocks,
        "title": derive_title(raw_text),
        "digest": derive_digest(raw_text),
        "warnings": warnings + ["未改写：只做了分节、配图与排版"],
        "source": "heuristic",
    }


def _scene(scene: str | None, text: str) -> str:
    if scene and scene != "auto":
        return scene
    score = {
        "family": len(re.findall(r"孩子|女儿|儿子|宝宝|幼儿园|作业|小朋友|妈妈|爸爸|奶奶|外婆", text)),
        "travel": len(re.findall(r"出发|高铁|机场|酒店|景区|门票|自驾|公里|行李|民宿", text)),
        "anniversary": len(re.findall(r"周年|纪念|第一次|那年|结婚|生日|在一起|相识", text)),
        "daily": len(re.findall(r"今天|早上|晚上|楼下|做饭|散步|窗|雨", text)),
    }
    best = max(score, key=lambda k: score[k])
    return best if score[best] > 0 else "daily"


def _expand_llm(raw_text: str, images: list[str], profile: dict, scene: str) -> dict:
    allowed = COMMON_BLOCKS + SCENE_BLOCKS.get(scene, [])
    img_lines = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(images)) or "  （无）"
    prompt = f"""把用户的原始文案整理成微信公众号图文的结构化数据。

## 写作者的声音（决定用词与句子节奏）
{profile_mod.contract(profile, scene)}

## 必须遵守
{profile_mod.contract_rules(profile)}
- 只能使用这些块型：{", ".join(allowed)}
- 每个块的字段必须符合块型定义；不确定就不要用。
- 图片只能引用下面给出的路径，不要编造路径，也不要重复使用同一张。
- 只在必要处分节，一节 2–4 段。分节标题要短（≤12 字），不要写成「关于……的思考」。
- 原文里的原话、数字、时间、地点一律照抄。

## 可用图片（按顺序使用）
{img_lines}

## 原始文案
{raw_text}

## 输出
只输出 JSON，不要解释：
{{"title": "≤32字", "digest": "≤120字", "blocks": [{{"type": "...", ...}}]}}
块型字段参考：p/lead/h2/h3 {{text}}；quote {{text, source}}；list {{items[], ordered}}；
callout {{title, items[]}}；image {{src, caption}}；images {{srcs[], caption}}；
divider {{glyph}}；footer {{text}}；
photo_polaroid {{src, caption}}；kid_quote {{text, nickname, age}}；
checklist {{items:[{{text,done}}]}}；dialogue {{lines:[{{side,text,who}}]}}；
timeline {{items:[{{time,title,desc}}]}}；route_table {{head[], rows:[{{time,route}}]}}；
weather_card {{date,city,temp,weather,note}}；stamp {{city,date}}；
drop_cap {{text}}；margin_note {{text}}；letter_paper {{text}}；sign_off {{signature,date}}；
countdown_card {{number,unit,label}}；ticket_stub {{title,date,city,years}}；
compare_pair {{a,b,cap_a,cap_b}}；memory_band {{items:[{{year,text}}]}}"""

    raw = complete(prompt, temperature=0.35, max_tokens=2000)
    data = _extract_json(raw)
    if not isinstance(data, dict) or not isinstance(data.get("blocks"), list):
        raise ValueError("模型没有返回合法 JSON")

    blocks = []
    used_imgs = 0
    for b in data["blocks"]:
        if not isinstance(b, dict):
            continue
        t = (b.get("type") or "p").lower()
        if t not in allowed:
            t = "p"
        b["type"] = t
        # 图片路径必须来自用户输入，模型给的一律覆盖
        if t in ("image", "photo_polaroid"):
            if used_imgs < len(images):
                b["src"] = images[used_imgs]
                used_imgs += 1
            else:
                continue
        if t == "images":
            take = images[used_imgs : used_imgs + 2]
            if len(take) < 2:
                continue
            b["srcs"] = take
            used_imgs += 2
        blocks.append(b)

    if not blocks:
        raise ValueError("模型返回的 blocks 全部不可用")

    return {
        "blocks": blocks,
        "title": _clip(data.get("title") or derive_title(raw_text), TITLE_MAX),
        "digest": _clip(data.get("digest") or derive_digest(raw_text), DIGEST_MAX),
        "warnings": [],
        "source": "llm",
    }


# ------------------------------------------------------------------ 降级
def heuristic(raw_text: str, images: list[str], scene: str = "daily") -> list[dict]:
    """无模型时的确定性排版：分段、识别短行作小标题、按比例插图。"""
    text = (raw_text or "").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [p.strip() for p in text.split("\n") if p.strip()]

    blocks: list[dict] = []
    if paras:
        blocks.append({"type": "lead", "text": paras[0]})
        paras = paras[1:]

    # 图按段落均匀分配，多出来的放到双图块
    body_n = max(len(paras), 1)
    per = max(1, body_n // max(len(images), 1)) if images else 0
    img_i = 0
    h2_n = 0

    for i, p in enumerate(paras):
        flat = p.replace("\n", " ").strip()
        if len(flat) <= 14 and not flat.endswith(("。", "！", "？", "…")):
            blocks.append({"type": "h2", "text": flat})
            h2_n += 1
        else:
            blocks.append({"type": "p", "text": p})

        if images and per and (i + 1) % per == 0 and img_i < len(images):
            # 前两张留给双图块，观感更好
            if img_i == 0 and len(images) >= 2:
                blocks.append(
                    {"type": "images", "srcs": images[:2], "caption": ""}
                )
                img_i = 2
            else:
                blocks.append({"type": "image", "src": images[img_i]})
                img_i += 1

    while img_i < len(images):
        blocks.append({"type": "image", "src": images[img_i]})
        img_i += 1

    blocks = _scene_flourish(blocks, scene)
    return blocks


def _scene_flourish(blocks: list[dict], scene: str) -> list[dict]:
    """保真模式下也给场景留一个落点，否则四个包等于白做。"""
    if not blocks:
        return blocks
    body_text = "\n".join(b.get("text", "") for b in blocks if b.get("text"))
    if scene == "daily" and len(body_text) >= 60:
        # 首字下沉更适合开篇第一段
        for b in blocks:
            if b["type"] == "p":
                b["type"] = "drop_cap"
                break
    if scene == "travel" and len(blocks) >= 6:
        blocks.insert(3, {"type": "divider", "glyph": "· · ·"})
    if scene == "family" and re.search(r"[「“\"].{2,20}[」”\"]", body_text):
        blocks.insert(min(3, len(blocks)), {"type": "divider", "glyph": "· · ·"})
    return blocks


# ------------------------------------------------------------------ 标题/摘要
def derive_title(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if not text:
        return ""
    first = re.split(r"[。！？\n]", text)[0].strip()
    if 0 < len(first) <= TITLE_MAX:
        return first
    return _clip(first or text, TITLE_MAX)


def derive_digest(raw_text: str) -> str:
    text = re.sub(r"\s+", " ", (raw_text or "").strip())
    return _clip(text, DIGEST_MAX)


def _clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"
