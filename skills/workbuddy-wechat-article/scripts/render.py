"""Render semantic article blocks into WeChat-safe inline HTML.

The renderer never reads colours from article data; every visual choice comes
from ``themes.py``.  Unknown blocks degrade to a plain paragraph or list, and
unsupported CSS (flex/grid/position/transform/gradients) is rejected rather
than shipped to the WeChat editor.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import blocks
import themes

FORBIDDEN = (
    "display:flex", "display: grid", "display:grid", "position:absolute",
    "position:fixed", "transform:", "linear-gradient", "radial-gradient",
    "calc(", "::before", "::after",
)


class RenderError(ValueError):
    """Raised when blocks or rendered HTML violate the WeChat contract."""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def nl(value: Any) -> str:
    text = esc(value).replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "<br/>")


def _text(block: dict[str, Any], key: str = "text") -> str:
    value = block.get(key)
    return value if isinstance(value, str) else ""


def _items(block: dict[str, Any]) -> list[str]:
    value = block.get("items")
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _source(block: dict[str, Any], key: str, image_map: dict[str, str] | None) -> str:
    value = block.get(key)
    if not isinstance(value, str) or not value:
        return ""
    return (image_map or {}).get(value, value)


def _img(src: str, caption: str, style: str, alt: str = "") -> str:
    if not src:
        return ""
    caption_html = f'<section style="{style}">{nl(caption)}</section>' if caption else ""
    return f'<img src="{esc(src)}" alt="{esc(alt or caption)}" style="display:block;width:100%;height:auto;" />{caption_html}'


def _p(text: str, style: str) -> str:
    return f'<p style="{style}">{nl(text)}</p>'


def _block_common(block: dict[str, Any], theme: dict[str, Any], image_map: dict[str, str] | None) -> str:
    kind = str(block.get("type", ""))
    accent = theme["accent"]
    soft = theme["accent_soft"]
    rule = theme["rule"]
    sub = theme["sub"]
    gap = theme["gap"]
    radius = theme["radius"]

    if kind == "lead":
        return _p(
            _text(block),
            f"margin:0 0 {gap}px;padding:0 0 0 14px;border-left:3px solid {accent};"
            f"font-size:{theme['body'] + 1}px;line-height:{theme['line']};color:{theme['text']};",
        )
    if kind == "p":
        return _p(
            _text(block),
            f"margin:0 0 {gap}px;font-size:{theme['body']}px;line-height:{theme['line']};"
            f"color:{theme['text']};letter-spacing:{theme['tracking']};",
        )
    if kind == "h2":
        return (
            f'<section style="margin:{gap + 4}px 0 {gap - 4}px;">'
            f'<section style="width:28px;height:2px;background:{accent};margin:0 0 10px;"></section>'
            + _p(
                _text(block),
                f"margin:0;font-size:19px;line-height:1.6;font-weight:700;color:{theme['text']};",
            )
            + "</section>"
        )
    if kind == "h3":
        return _p(
            _text(block),
            f"margin:{gap}px 0 10px;font-size:17px;line-height:1.6;font-weight:700;color:{accent};",
        )
    if kind == "footer":
        return _p(
            _text(block),
            f"margin:{gap}px 0 0;font-size:13px;line-height:1.8;color:{sub};text-align:center;",
        )
    if kind == "quote":
        text = _text(block)
        source = _text(block, "source")
        source_html = (
            f'<section style="margin-top:8px;font-size:12.5px;color:{sub};text-align:right;">— {nl(source)}</section>'
            if source else ""
        )
        return (
            f'<section style="margin:0 0 {gap}px;padding:14px 16px;background:{theme["paper"]};'
            f'border-left:3px solid {accent};border-radius:{radius}px;">'
            + _p(text, f"margin:0;font-size:{theme['body']}px;line-height:{theme['line']};color:{sub};")
            + source_html
            + "</section>"
        )
    if kind in {"list", "checklist"}:
        rows = []
        for item in _items(block):
            if kind == "checklist":
                box = (
                    f'<span style="display:inline-block;width:15px;height:15px;border:1.5px solid {accent};'
                    f'border-radius:4px;vertical-align:-2px;margin-right:9px;text-align:center;'
                    f'font-size:11px;line-height:15px;color:{accent};">✓</span>'
                )
            else:
                box = f'<span style="color:{accent};margin-right:9px;">·</span>'
            rows.append(
                f'<section style="margin:0 0 7px;font-size:{theme["body"]}px;line-height:1.9;'
                f'color:{theme["text"]};">{box}{nl(item)}</section>'
            )
        return f'<section style="margin:0 0 {gap}px;">{"".join(rows)}</section>'
    if kind == "callout":
        title = _text(block, "title")
        title_html = (
            f'<section style="font-size:14px;font-weight:700;color:{accent};margin:0 0 6px;">{nl(title)}</section>'
            if title else ""
        )
        rows = "".join(
            f'<section style="margin:0 0 6px;font-size:14.5px;line-height:1.85;color:{theme["text"]};">{nl(item)}</section>'
            for item in _items(block)
        )
        return (
            f'<section style="margin:0 0 {gap}px;padding:16px;background:{soft};'
            f'border:1px solid {rule};border-radius:{radius}px;">{title_html}{rows}</section>'
        )
    if kind == "image":
        src = _source(block, "src", image_map)
        caption = _text(block, "caption")
        return (
            f'<section style="margin:0 0 {gap}px;">'
            + _img(src, caption, f"margin-top:8px;font-size:12.5px;color:{sub};text-align:center;")
            + "</section>"
        )
    if kind == "divider":
        return f'<section style="height:1px;background:{rule};margin:{gap + 6}px 0;"></section>'
    if kind == "code":
        return (
            f'<section style="margin:0 0 {gap}px;padding:14px 16px;background:{soft};'
            f'border-radius:{radius}px;font-family:Consolas,Menlo,monospace;font-size:13.5px;'
            f'line-height:1.8;color:{theme["text"]};overflow-wrap:break-word;">{nl(_text(block))}</section>'
        )
    return ""


def _family(block: dict[str, Any], theme: dict[str, Any], image_map: dict[str, str] | None) -> str:
    kind = str(block.get("type", ""))
    accent = theme["accent"]
    soft = theme["accent_soft"]
    gap = theme["gap"]
    if kind == "photo_polaroid":
        src = _source(block, "src", image_map)
        if not src:
            return ""
        caption = _text(block, "caption")
        caption_html = (
            f'<section style="font-size:12.5px;color:{theme["sub"]};text-align:center;padding-top:8px;">{nl(caption)}</section>'
            if caption else ""
        )
        return (
            f'<section style="text-align:center;margin:0 0 {gap}px;">'
            f'<section style="display:inline-block;width:82%;background:#FFFFFF;padding:9px 9px 12px;'
            f'border:1px solid {theme["rule"]};box-shadow:{theme["shadow"]};border-radius:2px;">'
            f'<img src="{esc(src)}" alt="{esc(caption)}" style="display:block;width:100%;height:auto;" />'
            f'{caption_html}</section></section>'
        )
    if kind == "kid_quote":
        text = _text(block)
        nickname = _text(block, "nickname")
        age = block.get("age")
        chip = ""
        if nickname:
            label = f"{nickname} · {age}岁" if isinstance(age, int) else nickname
            chip = (
                f'<section style="margin-top:10px;"><span style="display:inline-block;background:{theme["chip_bg"]};'
                f'color:{theme["chip_text"]};font-size:12px;padding:3px 10px;border-radius:{theme["radius_pill"]}px;">'
                f"{esc(label)}</span></section>"
            )
        return (
            f'<section style="background:{soft};border-radius:{theme["radius"] + 2}px;padding:18px 18px 14px;'
            f'margin:0 0 {gap}px;">'
            f'<section style="font-size:34px;line-height:0.9;color:{accent};font-family:Georgia,serif;">“</section>'
            f'<section style="font-size:17px;line-height:1.9;color:{theme["text"]};">{nl(text)}</section>'
            f"{chip}</section>"
        )
    if kind == "dialogue":
        lines = block.get("lines")
        if not isinstance(lines, list):
            left = _text(block, "left")
            right = _text(block, "right")
            lines = [{"who": "left", "text": left}, {"who": "right", "text": right}]
        rendered = []
        for line in lines:
            if not isinstance(line, dict):
                continue
            text = line.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            who = str(line.get("who", "left")).lower()
            right = who in {"right", "me", "self", "我"}
            background = accent if right else soft
            color = "#FFFFFF" if right else theme["text"]
            rendered.append(
                f'<section style="text-align:{"right" if right else "left"};margin:8px 0;">'
                f'<section style="display:inline-block;max-width:78%;background:{background};color:{color};'
                f'border-radius:{theme["radius"] + 2}px;padding:10px 14px;font-size:15px;line-height:1.7;'
                f'text-align:left;">{nl(text)}</section></section>'
            )
        return "".join(rendered)
    return ""


def _travel(block: dict[str, Any], theme: dict[str, Any], image_map: dict[str, str] | None) -> str:
    kind = str(block.get("type", ""))
    accent = theme["accent"]
    sub = theme["sub"]
    rule = theme["rule"]
    gap = theme["gap"]
    if kind == "timeline":
        items = block.get("items")
        rows = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                time = item.get("time")
                title = item.get("title")
                if not isinstance(title, str):
                    continue
                time_html = f'<span style="font-weight:600;color:{accent};">{esc(time)}</span> ' if time else ""
                rows.append(
                    f'<section style="border-left:2px solid {rule};padding:0 0 16px 16px;margin-left:4px;">'
                    f'<section style="font-size:14.5px;line-height:1.8;color:{theme["text"]};">'
                    f'<span style="color:{accent};">•</span> {time_html}{nl(title)}</section></section>'
                )
        return f'<section style="margin:0 0 {gap}px;">{"".join(rows)}</section>'
    if kind == "route_table":
        rows = block.get("rows")
        body = []
        if isinstance(rows, list):
            for item in rows:
                if not isinstance(item, dict):
                    continue
                time = item.get("time", "")
                route = item.get("route", "")
                body.append(
                    f'<tr><td style="width:72px;padding:8px 0;color:{sub};font-size:12px;'
                    f'border-bottom:1px solid {rule};vertical-align:top;">{esc(time)}</td>'
                    f'<td style="padding:8px 0;border-bottom:1px solid {rule};color:{theme["text"]};'
                    f'font-size:14px;line-height:1.7;">{nl(route)}</td></tr>'
                )
        return (
            f'<table style="width:100%;border-collapse:collapse;margin:0 0 {gap}px;font-size:14px;">'
            f'{"".join(body)}</table>'
        )
    if kind == "weather_card":
        date = _text(block, "date")
        city = _text(block, "city")
        temp = block.get("temp", "")
        weather = _text(block, "weather")
        meta = " · ".join(part for part in (date, city) if part)
        return (
            f'<section style="background:{theme["accent_soft"]};border-radius:{theme["radius"] + 2}px;'
            f'padding:14px 16px;margin:0 0 {gap}px;">'
            f'<section style="font-size:12px;color:{sub};letter-spacing:2px;">{esc(meta)}</section>'
            f'<section style="margin-top:6px;"><span style="font-size:34px;font-weight:700;color:{accent};'
            f'font-family:Consolas,Menlo,monospace;">{esc(temp)}°</span>'
            f'<span style="font-size:13px;color:{sub};margin-left:8px;">{nl(weather)}</span></section></section>'
        )
    if kind == "stamp":
        city = _text(block, "city")
        date = _text(block, "date")
        return (
            f'<section style="text-align:center;margin:0 0 {gap}px;">'
            f'<section style="display:inline-block;width:72px;height:72px;border:2px dashed {accent};'
            f'border-radius:50%;text-align:center;color:{accent};font-size:10px;line-height:1.35;'
            f'padding-top:15px;box-sizing:border-box;">'
            f'<section style="font-size:14px;font-weight:700;">{nl(city)}</section>'
            f'<section>{nl(date)}</section></section></section>'
        )
    return ""


def _daily(block: dict[str, Any], theme: dict[str, Any], image_map: dict[str, str] | None) -> str:
    kind = str(block.get("type", ""))
    accent = theme["accent"]
    sub = theme["sub"]
    rule = theme["rule"]
    gap = theme["gap"]
    if kind == "drop_cap":
        text = _text(block)
        if not text:
            return ""
        first, rest = text[0], text[1:]
        return (
            f'<p style="margin:0 0 {gap}px;font-size:{theme["body"]}px;line-height:{theme["line"]};'
            f'color:{theme["text"]};letter-spacing:{theme["tracking"]};">'
            f'<span style="font-size:34px;line-height:1;color:{accent};font-weight:700;margin-right:2px;">'
            f"{esc(first)}</span>{nl(rest)}</p>"
        )
    if kind == "margin_note":
        note = _text(block, "note") or _text(block)
        return (
            f'<section style="background:#FFF9E6;border-radius:{theme["radius"] + 2}px;padding:16px;'
            f'margin:0 8px {gap}px;border:1px solid #F0E6C8;">'
            f'<section style="width:56px;height:10px;background:rgba(0,0,0,0.10);margin:0 auto 12px;"></section>'
            f'<section style="font-size:14px;line-height:1.9;color:#6B6355;">{nl(note)}</section></section>'
        )
    if kind == "letter_paper":
        return (
            f'<section style="border-left:1px solid {rule};padding-left:16px;margin:0 0 {gap}px;">'
            f'<section style="font-family:{theme["font"]};font-size:16px;line-height:2.1;'
            f'color:{theme["text"]};text-indent:2em;">{nl(_text(block))}</section></section>'
        )
    if kind == "sign_off":
        signature = _text(block, "signature")
        date = _text(block, "date")
        lines = "<br/>".join(part for part in (esc(signature), esc(date)) if part)
        return (
            f'<section style="margin:{gap + 8}px 0 8px;text-align:right;">'
            f'<section style="width:36px;height:1px;background:{rule};margin:0 0 12px auto;"></section>'
            f'<section style="font-family:{theme["font"]};font-size:14px;color:{sub};line-height:1.9;">'
            f"{lines}</section></section>"
        )
    return ""


def _anniversary(block: dict[str, Any], theme: dict[str, Any], image_map: dict[str, str] | None) -> str:
    kind = str(block.get("type", ""))
    accent = theme["accent"]
    sub = theme["sub"]
    gap = theme["gap"]
    if kind == "countdown_card":
        number = block.get("number", "")
        unit = _text(block, "unit")
        label = _text(block, "label")
        return (
            f'<section style="text-align:center;padding:24px 0;margin:0 0 {gap}px;">'
            f'<section style="font-size:46px;line-height:1;font-weight:700;color:{accent};'
            f'font-family:Georgia,serif;">{esc(number)}</section>'
            f'<section style="font-size:12px;letter-spacing:3px;color:{sub};margin-top:10px;">{nl(unit)}</section>'
            f'<section style="font-size:14px;color:#6B5B5B;margin-top:6px;">{nl(label)}</section></section>'
        )
    if kind == "ticket_stub":
        title = _text(block, "title")
        date = _text(block, "date")
        city = _text(block, "city")
        years = block.get("years", "")
        meta = " · ".join(part for part in (date, city) if part)
        return (
            f'<section style="background:{theme["accent_soft"]};border:1px solid {theme["rule"]};'
            f'border-radius:{theme["radius"] + 4}px;font-size:0;margin:0 0 {gap}px;">'
            f'<section style="display:inline-block;width:66%;vertical-align:top;padding:16px;box-sizing:border-box;">'
            f'<section style="font-size:16px;font-weight:600;color:{accent};">{nl(title)}</section>'
            f'<section style="font-size:12px;color:{sub};margin-top:6px;">{esc(meta)}</section></section>'
            f'<section style="display:inline-block;width:30%;vertical-align:top;padding:16px 10px;'
            f'border-left:1px dashed {accent};text-align:center;box-sizing:border-box;">'
            f'<section style="font-size:24px;color:{accent};">{esc(years)}</section>'
            f'<section style="font-size:11px;color:{sub};letter-spacing:2px;">YEARS</section></section></section>'
        )
    if kind == "compare_pair":
        first = _source(block, "a", image_map)
        second = _source(block, "b", image_map)
        cap_a = _text(block, "cap_a")
        cap_b = _text(block, "cap_b")
        cells = []
        for src, caption in ((first, cap_a), (second, cap_b)):
            if not src:
                continue
            cells.append(
                f'<section style="display:inline-block;width:48%;vertical-align:top;margin:0 1%;">'
                f'<img src="{esc(src)}" alt="{esc(caption)}" style="display:block;width:100%;height:auto;border-radius:2px;" />'
                f'<section style="font-size:12px;color:{sub};text-align:center;margin-top:6px;">{nl(caption)}</section></section>'
            )
        return (
            f'<section style="font-size:0;text-align:center;margin:0 0 {gap}px;">'
            + "".join(cells)
            + "</section>"
        ) if cells else ""
    if kind == "memory_band":
        year = block.get("year", "")
        return (
            f'<section style="margin:0 0 14px;border-bottom:1px solid {theme["rule"]};'
            f'padding:0 0 12px 64px;text-indent:-64px;font-size:15px;line-height:1.8;color:{theme["text"]};">'
            f'<span style="display:inline-block;width:64px;font-family:Georgia,serif;font-size:18px;'
            f'font-weight:700;color:{accent};text-indent:0;">{esc(year)}</span> {nl(_text(block))}</section>'
        )
    return ""


SCENE_RENDERERS = {
    "family": _family,
    "travel": _travel,
    "daily": _daily,
    "anniversary": _anniversary,
}

COMMON_KINDS = {
    "lead", "p", "h2", "h3", "footer", "quote", "list", "checklist",
    "callout", "image", "divider", "code",
}


def _as(kind: str, **fields: Any) -> dict[str, Any]:
    return {"type": kind, **fields}


def _generic_scene(block: dict[str, Any], theme: dict[str, Any], image_map: dict[str, str] | None) -> str:
    """Render a scene block with the generic skeleton of the current scene."""
    kind = str(block.get("type", ""))
    if kind == "photo_polaroid":
        return _block_common(_as("image", src=block.get("src"), caption=_text(block, "caption")), theme, image_map)
    if kind == "kid_quote":
        source = _text(block, "nickname")
        age = block.get("age")
        if isinstance(age, int) and source:
            source = f"{source} · {age}岁"
        return _block_common(_as("quote", text=_text(block), source=source), theme, image_map)
    if kind == "dialogue":
        lines = block.get("lines")
        items = []
        if isinstance(lines, list):
            for line in lines:
                if isinstance(line, dict) and isinstance(line.get("text"), str):
                    items.append(f"{line.get('who', '')}：{line['text']}".strip("："))
        return _block_common(_as("list", items=items), theme, image_map) if items else ""
    if kind == "timeline":
        items = []
        for item in block.get("items", []) if isinstance(block.get("items"), list) else []:
            if isinstance(item, dict) and isinstance(item.get("title"), str):
                time = item.get("time")
                items.append((f"{time} " if time else "") + item["title"])
        return _block_common(_as("list", items=items), theme, image_map) if items else ""
    if kind == "route_table":
        items = []
        for row in block.get("rows", []) if isinstance(block.get("rows"), list) else []:
            if isinstance(row, dict):
                items.append(" · ".join(str(row.get(key, "")) for key in ("time", "route")).strip(" ·"))
        return _block_common(_as("list", items=items), theme, image_map) if items else ""
    if kind == "weather_card":
        meta = " · ".join(part for part in (_text(block, "date"), _text(block, "city")) if part)
        items = [f"{block.get('temp', '')}° {_text(block, 'weather')}".strip()]
        return _block_common(_as("callout", title=meta, items=items), theme, image_map)
    if kind == "stamp":
        return _block_common(
            _as("p", text=" · ".join(part for part in (_text(block, "city"), _text(block, "date")) if part)),
            theme, image_map,
        )
    if kind == "drop_cap":
        return _block_common(_as("p", text=_text(block)), theme, image_map)
    if kind == "margin_note":
        return _block_common(_as("callout", items=[_text(block, "note") or _text(block)]), theme, image_map)
    if kind == "letter_paper":
        return _block_common(_as("p", text=_text(block)), theme, image_map)
    if kind == "sign_off":
        return _block_common(
            _as("footer", text=" · ".join(part for part in (_text(block, "signature"), _text(block, "date")) if part)),
            theme, image_map,
        )
    if kind == "countdown_card":
        text = " ".join(str(block.get(key, "")) for key in ("number", "unit", "label")).strip()
        return _block_common(_as("h2", text=text), theme, image_map)
    if kind == "ticket_stub":
        meta = " · ".join(part for part in (_text(block, "date"), _text(block, "city")) if part)
        years = block.get("years", "")
        items = [meta] + ([f"{years} 年"] if years != "" else [])
        return _block_common(_as("callout", title=_text(block, "title"), items=items), theme, image_map)
    if kind == "compare_pair":
        first = _block_common(
            _as("image", src=block.get("a"), caption=_text(block, "cap_a")), theme, image_map
        )
        second = _block_common(
            _as("image", src=block.get("b"), caption=_text(block, "cap_b")), theme, image_map
        )
        return first + second
    if kind == "memory_band":
        text = (_text(block, "year") + " " + _text(block)).strip()
        return _block_common(_as("p", text=text), theme, image_map)
    return ""


def render_block(
    block: dict[str, Any],
    theme: dict[str, Any],
    image_map: dict[str, str] | None = None,
    scene: str | None = None,
) -> str:
    kind = str(block.get("type", ""))
    if kind in COMMON_KINDS:
        return _block_common(block, theme, image_map)
    scene = scene or themes.DEFAULT_SCENE
    if kind in themes.SCENE_BLOCKS.get(scene, set()):
        return SCENE_RENDERERS[scene](block, theme, image_map)
    generic = _generic_scene(block, theme, image_map)
    if generic:
        return generic
    # Unknown future blocks: preserve whatever prose they carry instead of
    # dropping the author's text.
    text = _text(block)
    if text:
        return _p(
            text,
            f"margin:0 0 {theme['gap']}px;font-size:{theme['body']}px;line-height:{theme['line']};"
            f"color:{theme['text']};",
        )
    items = _items(block)
    if items:
        rows = "".join(
            f'<section style="margin:0 0 7px;font-size:{theme["body"]}px;line-height:{theme["line"]};'
            f'color:{theme["text"]};">· {nl(item)}</section>'
            for item in items
        )
        return f'<section style="margin:0 0 {theme["gap"]}px;">{rows}</section>'
    return ""


def render_article(
    document: dict[str, Any],
    image_map: dict[str, str] | None = None,
    scene: str | None = None,
    profile: dict[str, Any] | None = None,
) -> tuple[str, list[str], dict[str, Any]]:
    scene = scene or document.get("scene") or "daily"
    if scene == "auto":
        scene = "daily"
    theme = themes.theme_for(scene)
    theme = dict(theme)
    whitespace = (profile or {}).get("typesetting", {}).get("whitespace")
    if whitespace == "tight":
        theme["gap"] = max(10, round(theme["gap"] * 0.7))
    elif whitespace == "airy":
        theme["gap"] = round(theme["gap"] * 1.3)
    warnings: list[str] = []
    forbid = set((profile or {}).get("typesetting", {}).get("forbid_blocks", []))
    for block in document["blocks"]:
        kind = str(block.get("type", ""))
        if kind in forbid:
            warnings.append(f"block 类型 {kind} 在作者偏好中被禁用，仍按通用样式渲染")
        owner = next((name for name, kinds in themes.SCENE_BLOCKS.items() if kind in kinds), None)
        if owner and owner != scene:
            warnings.append(f"{kind} 没有 {scene} 专属皮肤，已按当前场景的通用骨架渲染")
    body = "".join(render_block(block, theme, image_map, scene) for block in document["blocks"])
    html_text = (
        f'<section style="font-family:{theme["font"]};font-size:{theme["body"]}px;'
        f'line-height:{theme["line"]};color:{theme["text"]};letter-spacing:{theme["tracking"]};'
        f'overflow-wrap:break-word;word-break:break-word;">{body}</section>'
    )
    lowered = html_text.lower()
    for fragment in FORBIDDEN:
        if fragment in lowered:
            raise RenderError(f"渲染结果包含微信不支持的 CSS：{fragment}")
    meta = {
        "scene": scene,
        "scene_label": theme["label"],
        "chars": blocks.content_length(blocks.text_content(document["blocks"])),
        "blocks": len(document["blocks"]),
        "warnings": warnings,
    }
    return html_text, warnings, meta


def _image_rows(images: list[dict[str, Any]] | None) -> str:
    if not images:
        return '<p class="muted">本版没有正文图片。</p>'
    rows = []
    for image in images:
        status = "无损" if image.get("lossless") else "有损"
        detail = image.get("reason") or ""
        rows.append(
            f'<tr><td>{esc(Path(str(image.get("src", ""))).name)}</td>'
            f'<td>{esc(image.get("src_px", ""))} → {esc(image.get("output_px", ""))}</td>'
            f'<td>{image.get("output_bytes", 0):,} B</td>'
            f'<td>{esc(status)}{"：" + esc(detail) if detail else ""}</td></tr>'
        )
    return (
        '<table><thead><tr><th>图片</th><th>像素</th><th>体积</th><th>结论</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def render_preview(
    document: dict[str, Any],
    article: str,
    meta: dict[str, Any],
    images: list[dict[str, Any]] | None = None,
    voice_report: dict[str, Any] | None = None,
) -> str:
    title = document.get("title") or "公众号文章预览"
    author = document.get("author") or ""
    profile = document.get("profile")
    if not author and isinstance(profile, dict):
        author = profile.get("identity", {}).get("name", "")
    voice_html = ""
    if voice_report:
        scores = voice_report.get("scores", {})
        voice_html = (
            '<details open><summary>AI 味自检</summary>'
            f'<p>最终 <b>{scores.get("final", "-")}</b>（AI {scores.get("ai", "-")} / 人味 {scores.get("human", "-")}）'
            f' · {esc(scores.get("band", ""))}</p>'
            f'<p>问题 {len(voice_report.get("issues", []))} 条，保留 {len(voice_report.get("keep", []))} 处，'
            f'可定点改写 {len(voice_report.get("targets", []))} 句。</p></details>'
        )
    warnings = "".join(f"<li>{esc(item)}</li>" for item in meta.get("warnings", []))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · 公众号预览</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0 auto;padding:18px;max-width:1100px;background:#F0F1EE;color:#292D29;
font:15px/1.6 -apple-system,"Microsoft YaHei",sans-serif}}
header,main,aside{{background:#fff;border-radius:10px;padding:20px;margin:0 0 18px}}
header h1{{margin:0 0 6px;font-size:24px}} header p{{margin:0;color:#667}}
.tools{{margin:10px 0 0}}
.tools label{{margin-right:14px;cursor:pointer}}
#narrow:checked ~ main{{max-width:375px}} #wide:checked ~ main{{max-width:430px}}
main{{max-width:430px;margin:0 auto 18px;padding:0;background:transparent}}
main .paper{{background:#fff;border-radius:10px;padding:22px;box-shadow:0 2px 12px rgba(0,0,0,.06)}}
aside table{{width:100%;border-collapse:collapse;font-size:13px}}
aside th,aside td{{text-align:left;padding:6px 8px;border-bottom:1px solid #eee;vertical-align:top}}
aside th{{color:#667;font-weight:600}}
details{{margin:10px 0}} summary{{cursor:pointer;font-weight:600}}
.muted{{color:#778}} code{{font-family:Consolas,monospace}}
</style></head>
<body>
<header><h1>{esc(title)}</h1><p>{esc(author)} · {esc(meta.get("scene_label", ""))} ·
{meta.get("chars", 0)} 字 · {meta.get("blocks", 0)} 个 block</p>
<div class="tools"><label for="narrow">375px</label><label for="wide">430px</label></div></header>
<input type="radio" name="width" id="narrow"><label for="narrow">375px</label>
<input type="radio" name="width" id="wide" checked><label for="wide">430px</label>
<main><div class="paper">{article}</div></main>
<aside><details open><summary>本版信息</summary>
<ul>{warnings if warnings else "<li>无渲染告警</li>"}</ul>
<p class="muted">图片 {len(images or [])} 张。上传后需回读 CDN 像素才能确认是否真无损。</p>
{_image_rows(images)}</details>{voice_html}</aside>
</body></html>"""


def write_outputs(
    document: dict[str, Any],
    out_dir: str | Path,
    *,
    image_map: dict[str, str] | None = None,
    scene: str | None = None,
    profile: dict[str, Any] | None = None,
    images: list[dict[str, Any]] | None = None,
    voice_report: dict[str, Any] | None = None,
    extra_warnings: list[str] | None = None,
) -> dict[str, Any]:
    article, warnings, meta = render_article(document, image_map, scene, profile)
    warnings = list(extra_warnings or []) + warnings
    meta["warnings"] = warnings
    preview = render_preview(document, article, meta, images, voice_report)
    target = Path(out_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    article_path = target / "article.html"
    preview_path = target / "preview.html"
    article_path.write_text(article, encoding="utf-8")
    preview_path.write_text(preview, encoding="utf-8")
    info = {
        "ok": True,
        "articlePath": str(article_path),
        "previewPath": str(preview_path),
        "scene": meta["scene"],
        "sceneLabel": meta["scene_label"],
        "chars": meta["chars"],
        "blocks": meta["blocks"],
        "warnings": warnings,
        "articleBytes": len(article.encode("utf-8")),
        "images": images or [],
    }
    (target / "render.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return info
