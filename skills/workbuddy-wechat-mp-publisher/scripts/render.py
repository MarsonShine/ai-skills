"""结构化内容 → 微信公众号可接受的内联样式 HTML。

两个原则：
1. 语义与版式分离：block 只描述「这是什么」，视觉全部由 theme token 决定。
2. 每个专属块都有通用骨架：换主题时最差退化成普通卡片，绝不丢内容。

微信硬约束：只认内联 style；不支持 flex / grid / position / 伪元素 / JS；
渐变与 transform 不稳，一律不用。栅格用 inline-block + font-size:0 + 百分比宽。
"""

from __future__ import annotations

import html as _html
import json
import re

from themes import FONT_MONO, get_theme

MAX_WIDTH = "677px"


# ------------------------------------------------------------------ 基础工具
def esc(text) -> str:
    return _html.escape(str(text), quote=False)


def _rgba(hex_color: str, alpha: float) -> str:
    """#rrggbb → rgba(...)。微信不支持 8 位 hex，必须转成 rgba。"""
    h = (hex_color or "").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return f"rgba(0,0,0,{alpha})"
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def inline(text, t: dict) -> str:
    """轻量行内标记：**加粗**、==高亮==、`代码`、[文字](链接)。"""
    s = esc(text)
    s = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong style="font-weight:600;color:' + t["accent"] + r';">\1</strong>',
        s,
    )
    s = re.sub(
        r"==(.+?)==",
        r'<span style="background:' + t["highlight"] + r';padding:0 3px;'
        r'border-radius:2px;">\1</span>',
        s,
    )
    s = re.sub(
        r"`(.+?)`",
        '<span style="font-family:' + FONT_MONO + ';font-size:0.92em;'
        r'background:#f4f4f5;padding:1px 5px;border-radius:3px;">\1</span>',
        s,
    )
    s = re.sub(
        r"\[(.+?)\]\((https?://[^\s)]+)\)",
        r'<a href="\2" style="color:' + t["accent"] + r';text-decoration:none;'
        r'border-bottom:1px solid ' + t["accent"] + r';">\1</a>',
        s,
    )
    return s


def _p(text, t: dict, extra: str = "") -> str:
    style = (
        f"margin:0 0 18px;font-size:{t['body_size']};line-height:{t['line_height']};"
        f"color:{t['body_color']};letter-spacing:{t['letter_spacing']};"
        f"text-align:justify;{extra}"
    )
    return f'<p style="{style}">{inline(text, t)}</p>'


# ------------------------------------------------------------------ 通用块
def _dots(color: str, size: int = 4, gap: int = 9, margin: str = "34px 0") -> str:
    """三颗实心圆点。用它代替「· · ·」字符：字符点太小、间距靠字体，
    在浅色主题里实测几乎不可见；圆点尺寸和间距都可控。"""
    one = (
        f'<span style="display:inline-block;width:{size}px;height:{size}px;'
        f'border-radius:50%;background:{color};margin:0 {gap // 2}px;'
        'vertical-align:middle;"></span>'
    )
    return (
        f'<section style="margin:{margin};text-align:center;font-size:0;'
        f'line-height:0;">{one * 3}</section>'
    )


def b_h2(b: dict, t: dict, idx: int = 0) -> str:
    text = inline(b.get("text", ""), t)
    num = f"{idx:02d}" if t["numbered"] else ""
    key, scene = t["key"], t.get("scene")

    if key == "magazine":
        return (
            '<section style="margin:36px 0 18px;">'
            f'<section style="font-size:12px;letter-spacing:2px;color:{t["accent"]};'
            f'font-weight:600;font-family:{FONT_MONO};">{num}</section>'
            f'<section style="height:1px;background:{t["rule"]};margin:8px 0 10px;"></section>'
            f'<section style="font-size:20px;font-weight:700;color:#1f1d1a;'
            f'line-height:1.5;letter-spacing:1px;">{text}</section></section>'
        )
    if key == "minimal":
        return (
            '<section style="margin:44px 0 20px;text-align:center;">'
            f'<section style="font-size:17px;font-weight:600;color:#111;'
            f'letter-spacing:3px;">{text}</section>'
            f'<section style="width:26px;height:2px;background:{t["accent"]};'
            'margin:12px auto 0;"></section></section>'
        )
    if key == "tech":
        return (
            '<section style="margin:36px 0 16px;">'
            f'<section style="display:inline-block;background:{t["accent"]};'
            f'color:{t["accent_2"]};font-family:{FONT_MONO};font-size:11px;'
            'letter-spacing:1px;padding:3px 9px;border-radius:3px;">'
            f'{"SEC " + num if num else "SECTION"}</section>'
            f'<section style="font-size:19px;font-weight:700;color:{t["accent"]};'
            'line-height:1.5;margin-top:10px;">'
            f"{text}</section></section>"
        )
    # ---- 场景包
    if scene == "family":
        return (
            '<section style="margin:34px 0 16px;">'
            f'<section style="display:inline-block;background:{t["accent_soft"]};'
            f'color:{t["accent"]};font-size:13px;font-weight:700;letter-spacing:1px;'
            f'padding:5px 14px;border-radius:{t["radius_pill"]};">{text}</section>'
            "</section>"
        )
    if scene == "travel":
        return (
            f'<section style="margin:34px 0 16px;padding-left:12px;'
            f'border-left:3px solid {t["accent"]};font-size:18px;font-weight:700;'
            f'color:{t["accent"]};line-height:1.5;letter-spacing:1px;">{text}</section>'
        )
    if scene == "daily":
        return (
            '<section style="margin:40px 0 18px;text-align:center;">'
            f'<section style="font-size:14px;letter-spacing:6px;color:{t["sub_color"]};'
            f'font-family:{t["font"]};">{text}</section>'
            f'<section style="width:20px;height:1px;background:{t["accent"]};'
            'margin:10px auto 0;"></section></section>'
        )
    # anniversary 及兜底
    return (
        '<section style="margin:38px 0 18px;text-align:center;">'
        f'{_dots(t["accent_2"], 4, 10, margin="0 0 12px")}'
        f'<section style="font-size:17px;font-weight:600;color:{t["accent"]};'
        f'letter-spacing:3px;">{text}</section></section>'
    )


def b_h3(b: dict, t: dict, idx: int = 0) -> str:
    return (
        f'<section style="margin:26px 0 12px;font-size:16.5px;font-weight:600;'
        f'color:{t["accent"]};line-height:1.6;">{inline(b.get("text", ""), t)}</section>'
    )


def b_lead(b: dict, t: dict, idx: int = 0) -> str:
    text = inline(b.get("text", ""), t)
    scene = t.get("scene")
    if t["key"] == "minimal" or scene in ("daily", "anniversary"):
        color = "#111" if t["key"] == "minimal" else t["sub_color"]
        return (
            f'<section style="margin:0 0 26px;font-size:15px;line-height:1.95;'
            f'color:{color};letter-spacing:1px;text-align:center;">{text}</section>'
        )
    return (
        f'<section style="margin:0 0 26px;padding:16px 18px;'
        f'background:{t["accent_soft"]};border-left:3px solid {t["accent"]};'
        f'border-radius:0 {t["radius"]} {t["radius"]} 0;font-size:15px;'
        f'line-height:1.85;color:{t["body_color"]};letter-spacing:0.5px;">'
        f"{text}</section>"
    )


def b_p(b: dict, t: dict, idx: int = 0) -> str:
    return _p(b.get("text", ""), t)


def b_quote(b: dict, t: dict, idx: int = 0) -> str:
    text = inline(b.get("text", ""), t)
    src = b.get("source")
    src_html = (
        f'<section style="font-size:12px;color:{t["sub_color"]};margin-top:10px;'
        f'text-align:right;">—— {inline(src, t)}</section>' if src else ""
    )
    if t["key"] == "minimal" or t.get("scene") in ("daily", "anniversary"):
        return (
            '<section style="margin:28px 0;padding:0 8px;text-align:center;">'
            f'<section style="font-size:16px;line-height:1.95;color:{t["body_color"]};'
            f'letter-spacing:1px;">{text}</section>{src_html}</section>'
        )
    return (
        f'<section style="margin:26px 0;padding:18px 20px;'
        f'background:{t["accent_soft"]};border-radius:{t["radius"]};">'
        f'<section style="font-size:15px;line-height:1.9;color:{t["body_color"]};'
        f'letter-spacing:0.6px;">{text}</section>{src_html}</section>'
    )


def b_list(b: dict, t: dict, idx: int = 0) -> str:
    items = b.get("items") or []
    ordered = bool(b.get("ordered"))
    indent = 30 if ordered else 17
    rows = []
    for i, it in enumerate(items, 1):
        if ordered:
            # text-indent:0 必须显式写：inline-block 会继承父级的负 text-indent，
            # 把 "01" 画到盒子左侧外面被裁掉（实测序号完全不可见）。
            marker = (
                f'<span style="display:inline-block;min-width:22px;margin-right:8px;'
                f'text-indent:0;font-family:{FONT_MONO};font-size:13px;'
                f'color:{t["accent"]};font-weight:600;">{i:02d}</span>'
            )
        else:
            marker = (
                f'<span style="display:inline-block;width:5px;height:5px;'
                f'background:{t["accent"]};border-radius:50%;margin:0 10px 3px 2px;'
                'vertical-align:middle;"></span>'
            )
        rows.append(
            f'<section style="margin:0 0 12px;padding-left:{indent}px;'
            f'text-indent:-{indent}px;font-size:{t["body_size"]};'
            f'line-height:{t["line_height"]};color:{t["body_color"]};">'
            f"{marker}{inline(it, t)}</section>"
        )
    return '<section style="margin:0 0 20px;">' + "".join(rows) + "</section>"


def b_callout(b: dict, t: dict, idx: int = 0) -> str:
    title = b.get("title") or "划重点"
    items = b.get("items") or ([b["text"]] if b.get("text") else [])
    head = (
        f'<section style="font-size:13px;font-weight:700;letter-spacing:1.5px;'
        f'color:{t["accent"]};margin-bottom:10px;">{inline(title, t)}</section>'
    )
    body = "".join(
        f'<section style="font-size:14.5px;line-height:1.85;color:{t["body_color"]};'
        f'margin:0 0 6px;padding-left:15px;text-indent:-15px;">· {inline(x, t)}</section>'
        for x in items
    )
    if t["key"] == "tech":
        return (
            f'<section style="margin:22px 0;padding:16px 18px;background:{t["callout_bg"]};'
            f'border:1px solid {t["rule"]};border-top:2px solid {t["accent_2"]};'
            f'border-radius:{t["radius"]};">{head}{body}</section>'
        )
    return (
        f'<section style="margin:22px 0;padding:16px 18px;background:{t["callout_bg"]};'
        f'border:1px {t["rule_style"]} {t["rule"]};border-radius:{t["radius"]};">'
        f"{head}{body}</section>"
    )


def b_image(b: dict, t: dict, idx: int = 0) -> str:
    src = b.get("src", "")
    cap = b.get("caption")
    cap_html = (
        f'<section style="font-size:12px;color:{t["sub_color"]};text-align:center;'
        f'margin-top:8px;line-height:1.6;font-family:{t["caption_font"]};">'
        f"{inline(cap, t)}</section>" if cap else ""
    )
    return (
        f'<section style="margin:{t["gap"]} 0;">'
        f'<img src="{esc(src)}" style="width:100%;display:block;'
        f'border-radius:{t["radius"]};">{cap_html}</section>'
    )


def b_images(b: dict, t: dict, idx: int = 0) -> str:
    srcs = [s for s in (b.get("srcs") or []) if s]
    if not srcs:
        return ""
    if len(srcs) < 2:
        return b_image({"src": srcs[0], "caption": b.get("caption")}, t)
    if len(srcs) % 2 == 0 and len(srcs) <= 4:
        cells = []
        for i, s in enumerate(srcs):
            gap = "margin-right:2%;" if i % 2 == 0 else ""
            # 注意：style 属性的引号必须闭合，否则下一张图的 src 会被吞进属性值，
            # 表现为「双图只出一张」（原型里的真实 bug）。
            cells.append(
                f'<img src="{esc(s)}" style="width:49%;display:inline-block;'
                f"vertical-align:top;border-radius:{t['radius']};margin:0 0 2%;{gap}\">"
            )
        wrap = (
            f'<section style="font-size:0;line-height:0;margin:{t["gap"]} 0;">'
            + "".join(cells)
            + "</section>"
        )
    else:
        wrap = "".join(b_image({"src": s}, t) for s in srcs)
    cap = b.get("caption")
    if cap:
        wrap += (
            f'<section style="font-size:12px;line-height:1.6;color:{t["sub_color"]};'
            f'text-align:center;margin:-14px 0 {t["gap"]};'
            f'font-family:{t["caption_font"]};">{inline(cap, t)}</section>'
        )
    return wrap


def b_code(b: dict, t: dict, idx: int = 0) -> str:
    code = esc(b.get("text", ""))
    return (
        f'<section style="margin:20px 0;padding:14px 16px;background:#f6f7f9;'
        f'border-radius:{t["radius"]};overflow-x:auto;">'
        f'<pre style="margin:0;font-family:{FONT_MONO};font-size:13px;'
        f'line-height:1.7;color:#1f2937;white-space:pre-wrap;">{code}</pre></section>'
    )


def b_divider(b: dict, t: dict, idx: int = 0) -> str:
    glyph = (b.get("glyph") or "").strip()
    # 纯点类分隔符统一走圆点，避免字符点太小、颜色太淡
    if glyph and set(glyph.replace(" ", "")) <= {"·", ".", "•"}:
        return _dots(_rgba(t["accent"], 0.5), 4, 10)
    if glyph:
        return (
            f'<section style="margin:34px 0;text-align:center;font-size:16px;'
            f'letter-spacing:5px;color:{_rgba(t["accent"], 0.55)};">{esc(glyph)}</section>'
        )
    return (
        f'<section style="margin:34px 0;height:1px;'
        f'background:{_rgba(t["accent"], 0.22)};"></section>'
    )


def b_footer(b: dict, t: dict, idx: int = 0) -> str:
    return (
        f'<section style="margin:36px 0 8px;padding-top:16px;'
        f'border-top:1px solid {t["rule"]};font-size:12.5px;line-height:1.9;'
        f'color:{t["sub_color"]};letter-spacing:0.5px;">'
        f'{inline(b.get("text", ""), t)}</section>'
    )


# ------------------------------------------------------------------ 场景块
def b_photo_polaroid(b: dict, t: dict, idx: int = 0) -> str:
    """拍立得：白边 + 细边框（阴影被剥离时仍成立）。"""
    cap = b.get("caption")
    cap_html = (
        f'<section style="font-size:12.5px;color:{t["sub_color"]};text-align:center;'
        f'padding-top:9px;font-family:{t["caption_font"]};line-height:1.6;">'
        f"{inline(cap, t)}</section>" if cap else ""
    )
    return (
        '<section style="text-align:center;'
        f'margin:{t["gap"]} 0;">'
        f'<section style="display:inline-block;width:86%;background:#fff;'
        f'padding:9px 9px 13px;border:1px solid {t["card_border"]};'
        f'box-shadow:{t["shadow"]};border-radius:2px;text-align:left;">'
        f'<img src="{esc(b.get("src", ""))}" style="width:100%;display:block;">'
        f"{cap_html}</section></section>"
    )


def b_kid_quote(b: dict, t: dict, idx: int = 0) -> str:
    """童言卡：引号用真实字符，不用伪元素。"""
    nick = b.get("nickname") or ""
    age = b.get("age")
    chip = ""
    if nick:
        age_txt = f" · {age}岁" if age not in (None, "") else ""
        chip = (
            '<section style="margin-top:10px;">'
            f'<span style="display:inline-block;background:{t["chip_bg"]};'
            f'color:{t["chip_text"]};font-size:12px;padding:3px 10px;'
            f'border-radius:{t["radius_pill"]};">{esc(nick)}{age_txt}</span></section>'
        )
    return (
        f'<section style="background:{t["accent_soft"]};border-radius:{t["radius_lg"]};'
        f'padding:16px 18px 14px;margin:{t["gap"]} 0;">'
        f'<section style="font-size:40px;line-height:0.9;color:{t["accent"]};'
        'font-family:Georgia,serif;margin-bottom:2px;">“</section>'
        f'<section style="font-size:17px;line-height:1.9;color:{t["body_color"]};">'
        f'{inline(b.get("text", ""), t)}</section>{chip}</section>'
    )


def b_checklist(b: dict, t: dict, idx: int = 0) -> str:
    rows = []
    for raw in b.get("items") or []:
        item = raw if isinstance(raw, dict) else {"text": raw}
        done = bool(item.get("done"))
        mark = "✓" if done else ""
        color = t["sub_color"] if done else t["accent"]
        deco = "line-through" if done else "none"
        rows.append(
            '<section style="margin:7px 0;font-size:15px;line-height:1.9;'
            f'color:{t["body_color"]};text-decoration:{deco};">'
            f'<span style="display:inline-block;width:15px;height:15px;'
            f'border:1.5px solid {t["accent"]};border-radius:4px;'
            'vertical-align:-2px;margin-right:9px;text-align:center;'
            f'font-size:11px;line-height:15px;color:{color};">{mark}</span>'
            f'{inline(item.get("text", ""), t)}</section>'
        )
    return f'<section style="margin:{t["gap"]} 0;">{"".join(rows)}</section>'


def b_dialogue(b: dict, t: dict, idx: int = 0) -> str:
    """对话气泡：左右用 text-align 对齐 inline-block，不依赖 flex。"""
    blocks = []
    for line in b.get("lines") or []:
        text = inline(line.get("text", ""), t)
        left = (line.get("side") or "left") == "left"
        who = line.get("who")
        who_html = (
            f'<section style="font-size:11px;color:{t["sub_color"]};margin-bottom:4px;">'
            f"{esc(who)}</section>" if who else ""
        )
        bg = t["accent_soft"] if left else t["accent"]
        fg = t["body_color"] if left else "#ffffff"
        blocks.append(
            f'<section style="text-align:{"left" if left else "right"};margin:8px 0;">'
            f'<section style="display:inline-block;max-width:80%;background:{bg};'
            f'color:{fg};border-radius:{t["radius"]};padding:10px 14px;'
            f'font-size:15px;line-height:1.7;text-align:left;">{who_html}{text}</section>'
            "</section>"
        )
    return f'<section style="margin:{t["gap"]} 0;">{"".join(blocks)}</section>'


def b_timeline(b: dict, t: dict, idx: int = 0) -> str:
    """时间轴：border-left 当竖线，负 margin 的圆点压在线上。"""
    items = b.get("items") or []
    rows = []
    for n, it in enumerate(items):
        last = n == len(items) - 1
        desc = it.get("desc")
        desc_html = (
            f'<section style="font-size:14px;line-height:1.8;color:{t["body_color"]};'
            f'margin-top:4px;">{inline(desc, t)}</section>' if desc else ""
        )
        # 末项不画竖线、不留底距，否则时间轴会拖出一条无意义的尾巴。
        line = "" if last else f'border-left:2px solid {t["rule"]};'
        pad = "0 0 0 18px" if last else "0 0 18px 18px"
        rows.append(
            f'<section style="{line}padding:{pad};margin-left:6px;">'
            f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
            f'background:{t["accent"]};margin-left:-24px;margin-right:12px;'
            'vertical-align:middle;"></span>'
            f'<span style="font-weight:600;color:{t["accent"]};font-size:14px;'
            f'font-family:{t["num_font"]};">{esc(it.get("time", ""))}</span>'
            f'<span style="color:{t["body_color"]};font-size:15px;'
            f'margin-left:8px;">{inline(it.get("title", ""), t)}</span>'
            f"{desc_html}</section>"
        )
    return f'<section style="margin:{t["gap"]} 0;">{"".join(rows)}</section>'


def b_route_table(b: dict, t: dict, idx: int = 0) -> str:
    rows = []
    for r in b.get("rows") or []:
        if isinstance(r, (list, tuple)):
            time_v, route = (r + ["", ""])[:2]
        else:
            time_v, route = r.get("time", ""), r.get("route", "")
        rows.append(
            "<tr>"
            f'<td style="width:66px;padding:9px 0;color:{t["sub_color"]};font-size:12px;'
            f'border-bottom:1px solid {t["rule"]};vertical-align:top;">{esc(time_v)}</td>'
            f'<td style="padding:9px 0;color:{t["body_color"]};font-size:14.5px;'
            f'line-height:1.7;border-bottom:1px solid {t["rule"]};">{inline(route, t)}</td>'
            "</tr>"
        )
    head = b.get("head")
    head_html = ""
    if head and len(head) >= 2:
        head_html = (
            "<tr>"
            f'<td style="padding:0 0 8px;font-size:11px;letter-spacing:2px;'
            f'color:{t["sub_color"]};">{esc(head[0])}</td>'
            f'<td style="padding:0 0 8px;font-size:11px;letter-spacing:2px;'
            f'color:{t["sub_color"]};">{esc(head[1])}</td>'
            "</tr>"
        )
    return (
        f'<table style="width:100%;border-collapse:collapse;margin:{t["gap"]} 0;'
        f'font-family:{t["font"]};">{head_html}{"".join(rows)}</table>'
    )


def b_weather_card(b: dict, t: dict, idx: int = 0) -> str:
    meta = " · ".join(x for x in (b.get("date"), b.get("city")) if x)
    return (
        f'<section style="background:{t["accent_soft"]};border-radius:{t["radius_lg"]};'
        f'padding:14px 16px;margin:{t["gap"]} 0;">'
        f'<section style="font-size:12px;color:{t["sub_color"]};letter-spacing:2px;">'
        f"{esc(meta)}</section>"
        '<section style="margin-top:6px;">'
        f'<span style="font-size:34px;font-weight:700;color:{t["accent"]};'
        f'font-family:{FONT_MONO};line-height:1.1;">{esc(b.get("temp", ""))}</span>'
        f'<span style="font-size:13px;color:{t["sub_color"]};margin-left:10px;">'
        f'{esc(b.get("weather", ""))}</span></section>'
        f'<section style="font-size:14px;line-height:1.8;color:{t["body_color"]};'
        f'margin-top:8px;">{inline(b.get("note", ""), t)}</section></section>'
    )


def b_stamp(b: dict, t: dict, idx: int = 0) -> str:
    return (
        f'<section style="text-align:center;margin:{t["gap"]} 0;">'
        f'<section style="display:inline-block;min-width:76px;padding:14px 12px;'
        f'border:2px dashed {t["accent"]};border-radius:50%;text-align:center;'
        f'color:{t["accent"]};font-size:11px;line-height:1.5;">'
        f'<section style="font-size:15px;font-weight:700;letter-spacing:1px;">'
        f'{esc(b.get("city", ""))}</section>'
        f'<section style="color:{t["sub_color"]};">{esc(b.get("date", ""))}</section>'
        "</section></section>"
    )


def b_drop_cap(b: dict, t: dict, idx: int = 0) -> str:
    """首字下沉：放大 span + 负 vertical-align，不用 float。"""
    raw = b.get("text", "")
    first, rest = (raw[:1], raw[1:]) if raw else ("", "")
    return (
        f'<p style="margin:0 0 18px;font-size:{t["body_size"]};'
        f'line-height:{t["line_height"]};color:{t["body_color"]};'
        f'letter-spacing:{t["letter_spacing"]};text-align:justify;text-indent:0;">'
        f'<span style="display:inline-block;font-size:34px;line-height:1;'
        f'color:{t["accent"]};font-weight:700;margin-right:5px;'
        f'vertical-align:-2px;">{esc(first)}</span>{inline(rest, t)}</p>'
    )


def b_margin_note(b: dict, t: dict, idx: int = 0) -> str:
    """页边便签：顶部一块「胶带」压住上边缘；color 全部跟主题走。"""
    return (
        f'<section style="background:{_rgba(t["accent"], 0.06)};border-radius:3px;'
        f'padding:16px;margin:{t["gap"]} 8px;box-shadow:{t["shadow"]};'
        f'border:1px solid {_rgba(t["accent"], 0.22)};">'
        f'<section style="width:56px;height:11px;background:{_rgba(t["accent"], 0.18)};'
        'margin:-22px auto 10px;border-radius:1px;"></section>'
        f'<section style="font-size:14px;line-height:1.9;color:{t["body_color"]};">'
        f'{inline(b.get("text", ""), t)}</section></section>'
    )


def b_letter_paper(b: dict, t: dict, idx: int = 0) -> str:
    paras = [x for x in re.split(r"\n\s*\n", b.get("text", "")) if x.strip()]
    inner = "".join(
        f'<section style="font-family:{t["font"]};font-size:{t["body_size"]};'
        f'line-height:2.1;color:{t["body_color"]};text-indent:2em;'
        f'margin:0 0 14px;">{inline(p, t)}</section>'
        for p in paras
    )
    return (
        f'<section style="border-left:1px solid {t["rule"]};padding-left:16px;'
        f'margin:{t["gap"]} 0;">{inner}</section>'
    )


def b_sign_off(b: dict, t: dict, idx: int = 0) -> str:
    return (
        '<section style="margin:34px 0 8px;text-align:right;">'
        f'<section style="width:36px;height:1px;background:{t["rule"]};'
        'margin:0 0 12px auto;"></section>'
        f'<section style="font-family:{t["font"]};font-size:14px;'
        f'color:{t["sub_color"]};line-height:1.9;">{esc(b.get("signature", ""))}'
        f'<br>{esc(b.get("date", ""))}</section></section>'
    )


def b_countdown_card(b: dict, t: dict, idx: int = 0) -> str:
    return (
        f'<section style="text-align:center;padding:24px 0;margin:10px 0;">'
        f'<section style="font-size:46px;line-height:1;font-weight:700;'
        f'color:{t["num_color"]};font-family:{t["font"]};">{esc(b.get("number", ""))}</section>'
        f'<section style="font-size:12px;letter-spacing:3px;color:{t["sub_color"]};'
        f'margin-top:10px;">{esc(b.get("unit", ""))}</section>'
        f'<section style="font-size:14px;color:{t["sub_color"]};margin-top:6px;">'
        f'{inline(b.get("label", ""), t)}</section></section>'
    )


def b_ticket_stub(b: dict, t: dict, idx: int = 0) -> str:
    """票根：table 双栏，中缝虚线。用百分比宽 + padding 的 inline-block 会因
    content-box 撑破 100% 导致右栏换行（实测掉到标题下面），table 没这个问题。"""
    years = b.get("years")
    meta = " · ".join(x for x in (b.get("date"), b.get("city")) if x)
    return (
        f'<table style="width:100%;border-collapse:collapse;margin:{t["gap"]} 0;'
        f'background:{t["accent_soft"]};border:1px solid {t["card_border"]};'
        f'border-radius:{t["radius_lg"]};font-family:{t["font"]};">'
        "<tr>"
        f'<td style="width:64%;padding:16px;vertical-align:top;text-align:left;'
        f'border-right:1px dashed {_rgba(t["accent"], 0.45)};">'
        f'<section style="font-size:16px;font-weight:600;color:{t["accent"]};'
        f'line-height:1.6;">{inline(b.get("title", ""), t)}</section>'
        f'<section style="font-size:12px;color:{t["sub_color"]};margin-top:8px;">'
        f"{esc(meta)}</section></td>"
        '<td style="padding:16px 10px;vertical-align:middle;text-align:center;">'
        f'<section style="font-size:24px;line-height:1.2;color:{t["accent"]};'
        f'font-family:{t["font"]};">{esc(years if years is not None else "")}</section>'
        f'<section style="font-size:10px;letter-spacing:2px;color:{t["sub_color"]};">'
        f'{esc(b.get("unit", "YEARS"))}</section></td>'
        "</tr></table>"
    )


def b_compare_pair(b: dict, t: dict, idx: int = 0) -> str:
    def cell(src, cap):
        cap_html = (
            f'<section style="font-size:12px;color:{t["sub_color"]};text-align:center;'
            f'margin-top:7px;">{inline(cap, t)}</section>' if cap else ""
        )
        return (
            '<section style="display:inline-block;width:48%;vertical-align:top;'
            'margin:0 1%;">'
            f'<img src="{esc(src)}" style="width:100%;display:block;'
            f'border-radius:{t["radius"]};">{cap_html}</section>'
        )

    return (
        f'<section style="font-size:0;text-align:center;margin:{t["gap"]} 0;">'
        f'{cell(b.get("a", ""), b.get("cap_a"))}{cell(b.get("b", ""), b.get("cap_b"))}'
        "</section>"
    )


def b_memory_band(b: dict, t: dict, idx: int = 0) -> str:
    rows = []
    for it in b.get("items") or []:
        rows.append(
            f'<section style="margin:0 0 14px;border-bottom:1px solid {t["rule"]};'
            'padding:0 0 12px 58px;text-indent:-58px;font-size:15px;'
            f'line-height:1.85;color:{t["body_color"]};">'
            f'<span style="display:inline-block;width:58px;text-indent:0;'
            f'font-family:{t["font"]};font-size:17px;font-weight:700;'
            f'color:{t["accent"]};">{esc(it.get("year", ""))}</span>'
            f'{inline(it.get("text", ""), t)}</section>'
        )
    return f'<section style="margin:{t["gap"]} 0;">{"".join(rows)}</section>'


# ------------------------------------------------------------------ 注册表
BLOCKS = {
    # 通用
    "h2": b_h2, "h3": b_h3, "lead": b_lead, "p": b_p, "quote": b_quote,
    "list": b_list, "callout": b_callout, "image": b_image, "images": b_images,
    "code": b_code, "divider": b_divider, "footer": b_footer,
    # 家庭亲子
    "photo_polaroid": b_photo_polaroid, "kid_quote": b_kid_quote,
    "checklist": b_checklist, "dialogue": b_dialogue,
    # 旅行出门
    "timeline": b_timeline, "route_table": b_route_table,
    "weather_card": b_weather_card, "stamp": b_stamp,
    # 日常随笔
    "drop_cap": b_drop_cap, "margin_note": b_margin_note,
    "letter_paper": b_letter_paper, "sign_off": b_sign_off,
    # 纪念日
    "countdown_card": b_countdown_card, "ticket_stub": b_ticket_stub,
    "compare_pair": b_compare_pair, "memory_band": b_memory_band,
}

SCENE_BLOCKS = {
    "photo_polaroid", "kid_quote", "checklist", "dialogue",
    "timeline", "route_table", "weather_card", "stamp",
    "drop_cap", "margin_note", "letter_paper", "sign_off",
    "countdown_card", "ticket_stub", "compare_pair", "memory_band",
}

NUMBERED = {"h2"}


def render_body(blocks: list[dict], theme: dict) -> str:
    out, idx = [], 0
    for b in blocks or []:
        kind = (b.get("type") or "p").lower()
        fn = BLOCKS.get(kind)
        if fn is None:
            out.append(_p(str(b.get("text", "")) if b.get("text") else "", theme))
            continue
        if kind in NUMBERED:
            idx += 1
            out.append(fn(b, theme, idx))
        else:
            out.append(fn(b, theme, 0))
    return "".join(out)


def render_html(doc: dict, theme: str | None = None) -> str:
    """完整可提交的正文片段（微信只收片段，不要 <html> 外壳）。"""
    t = get_theme(theme or doc.get("theme"))
    body = render_body(doc.get("blocks") or [], t)
    head = ""
    if doc.get("title") and doc.get("show_title_inline"):
        head = (
            f'<section style="font-size:22px;font-weight:700;color:{t["num_color"]};'
            'line-height:1.45;letter-spacing:0.5px;margin:0 0 22px;">'
            f'{inline(doc["title"], t)}</section>'
        )
    return (
        f'<section style="max-width:{MAX_WIDTH};margin:0 auto;padding:{t["pad"]};'
        f'font-family:{t["font"]};font-size:{t["body_size"]};'
        f'color:{t["body_color"]};word-break:break-word;background:{t["paper"]};">'
        f"{head}{body}</section>"
    )


def render_page(doc: dict, theme: str | None = None) -> str:
    """本地预览：手机宽度外壳。预览不改变任何正文样式，保证「所见即线上」。"""
    t = get_theme(theme or doc.get("theme"))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(doc.get('title', '预览'))}</title>
<style>
  body{{margin:0;background:#ededed;font-family:-apple-system,sans-serif;}}
  .phone{{max-width:430px;margin:0 auto;background:{t['paper']};min-height:100vh;
         padding:22px 16px 60px;box-sizing:border-box;}}
  h1.tt{{font-size:22px;line-height:1.42;margin:4px 10px 8px;color:#111;}}
  .meta{{font-size:12px;color:#999;margin:0 10px 20px;}}
</style></head><body><div class="phone">
<h1 class="tt">{esc(doc.get('title', ''))}</h1>
<div class="meta">{esc(doc.get('author') or '')} · {t['label']}</div>
{render_html(doc, theme or doc.get('theme'))}
</div></body></html>"""


if __name__ == "__main__":  # 便于单独调试：python3 render.py doc.json magazine
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    doc = json.loads(raw)
    print(render_html(doc, sys.argv[2] if len(sys.argv) > 2 else None))
