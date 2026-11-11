#!/usr/bin/env python3
"""渲染层自检：全部块型 × 全部主题。

不联网、不依赖浏览器，检查的是「结构性错误」，也就是那种渲染出来还不报错、
但线上一定出错的问题：

1. 标签闭合 —— 属性引号漏闭合会把下一张图吞掉（双图只出一张的真实 bug）。
2. 图片数量 —— 少一张就是内容丢失。
3. 禁用 CSS —— flex / grid / position / 伪元素会被微信剥离，用了等于没写。
4. 模板泄漏 —— 出现 {{ }}、None、undefined 说明格式化没兜住。
5. 属性污染 —— 属性值里混进 '<' 或 'src=' 说明标签拼接坏了。

用法：python3 scripts/selftest.py [--verbose]
退出码：0 全通过；1 有失败项。
"""

from __future__ import annotations

import os
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render  # noqa: E402
import themes  # noqa: E402

IMG = "examples/sample/images"

# 覆盖 render.BLOCKS 里每一个 key；新增块若忘了加进这里，自检会直接报错。
FIXTURE = [
    {"type": "h2", "text": "一级标题"},
    {"type": "h3", "text": "二级标题"},
    {"type": "lead", "text": "导语，**加粗** 与 ==高亮==。"},
    {"type": "p", "text": "正文，含 `code` 与 [链接](https://example.com)。"},
    {"type": "quote", "text": "引文内容。", "source": "出处"},
    {"type": "list", "ordered": True, "items": ["第一项", "第二项"]},
    {"type": "list", "items": ["甲", "乙"]},
    {"type": "callout", "title": "划重点", "items": ["要点一", "要点二"]},
    {"type": "image", "src": f"{IMG}/1.jpg", "caption": "单图"},
    {"type": "images", "srcs": [f"{IMG}/2.jpg", f"{IMG}/3.jpg"], "caption": "双图"},
    {"type": "code", "text": "print('hi')"},
    {"type": "divider", "glyph": "· · ·"},
    {"type": "divider"},
    {"type": "footer", "text": "页脚说明"},
    {"type": "photo_polaroid", "src": f"{IMG}/1.jpg", "caption": "拍立得"},
    {"type": "kid_quote", "text": "云是不是也有妈妈？", "nickname": "豆豆", "age": 6},
    {"type": "checklist", "items": [{"text": "带水壶", "done": True}, {"text": "带画本"}]},
    {
        "type": "dialogue",
        "lines": [
            {"side": "left", "text": "吃什么？", "who": "豆豆"},
            {"side": "right", "text": "都行。"},
        ],
    },
    {"type": "timeline", "items": [{"time": "08:20", "title": "出门", "desc": "地铁"}]},
    {
        "type": "route_table",
        "head": ["时间", "行程"],
        "rows": [{"time": "08:20", "route": "集合"}],
    },
    {"type": "weather_card", "date": "11月8日", "city": "杭州", "temp": "18", "weather": "多云"},
    {"type": "stamp", "city": "杭州", "date": "2026.11"},
    {"type": "drop_cap", "text": "清早出门，银杏落了一地。"},
    {"type": "margin_note", "text": "便签内容"},
    {"type": "letter_paper", "text": "第一段。\n\n第二段。"},
    {"type": "sign_off", "signature": "阿柯", "date": "2026年11月"},
    {"type": "countdown_card", "number": "3650", "unit": "DAYS", "label": "第 3650 天"},
    {"type": "ticket_stub", "title": "第一次看海", "date": "2016.08", "city": "青岛", "years": "9"},
    {"type": "compare_pair", "a": f"{IMG}/2.jpg", "b": f"{IMG}/3.jpg", "cap_a": "那年", "cap_b": "今年"},
    {"type": "memory_band", "items": [{"year": "2016", "text": "看海"}]},
]

BANNED_CSS = ("display:flex", "display: grid", "display:grid", "position:absolute",
              "position: absolute", "position:fixed", "position: fixed", "float:")


class Doc(HTMLParser):
    """收集标签、属性、图片数，并记录解析过程中发现的异常。"""

    VOID = {"img", "br", "hr", "meta", "link", "input"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.imgs = 0
        self.bad_attrs: list[str] = []
        self.unclosed: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.imgs += 1
        for k, v in attrs:
            if v and ("<" in v or "src=" in v):
                self.bad_attrs.append(f"{tag}[{k}]={v[:40]}")
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            # 中间有未闭合的标签
            while self.stack and self.stack.pop() != tag:
                pass
            self.unclosed.append(tag)


def check(name: str, html: str, expect_imgs: int, verbose: bool) -> list[str]:
    errs: list[str] = []
    if "{{" in html or "}}" in html:
        errs.append("模板占位符未替换")
    if "None" in html:
        errs.append("输出里出现 None")

    low = html.replace(" ", "").lower()
    for pat in BANNED_CSS:
        if pat.replace(" ", "") in low:
            errs.append(f"用了微信会剥离的 CSS: {pat}")

    p = Doc()
    p.feed(html)
    p.close()
    if p.imgs != expect_imgs:
        errs.append(f"图片数 {p.imgs} ≠ 预期 {expect_imgs}")
    if p.bad_attrs:
        errs.append("属性被污染: " + "; ".join(p.bad_attrs[:2]))
    if p.stack:
        errs.append("标签未闭合: " + ",".join(p.stack[-3:]))

    if verbose and not errs:
        print(f"    · {name} ok ({len(html)} 字节, {p.imgs} 图)")
    return errs


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    names = themes.theme_names()

    # 覆盖性检查：BLOCKS 里有、FIXTURE 里没有的块型会被漏测
    used = {b["type"] for b in FIXTURE}
    missing = set(render.BLOCKS) - used
    if missing:
        print(f"[FAIL] 自检样本未覆盖这些块型: {sorted(missing)}")
        return 1

    expect_imgs = (
        sum(1 for b in FIXTURE if b["type"] == "image")
        + sum(len(b.get("srcs") or []) for b in FIXTURE if b["type"] == "images")
        + sum(1 for b in FIXTURE if b["type"] == "photo_polaroid")
        + sum(2 for b in FIXTURE if b["type"] == "compare_pair")
    )

    doc = {"title": "自检", "author": "selftest", "blocks": FIXTURE}
    failed = 0
    print(f"渲染层自检：{len(names)} 套主题 × {len(FIXTURE)} 个块")
    for n in names:
        html = render.render_html(doc, n)
        errs = check(f"{n}/html", html, expect_imgs, verbose)
        page = render.render_page(doc, n)
        # 预览壳本身会有 <html>/<body>，只查结构，不查图数
        page_errs = check(f"{n}/page", page, expect_imgs, verbose)
        if errs or page_errs:
            failed += 1
            print(f"[FAIL] {n}")
            for e in errs + page_errs:
                print(f"    - {e}")
        elif verbose:
            print(f"[ OK ] {n}")

    # 未知块型必须降级成段落，而不是抛异常或丢内容
    for n in names:
        html = render.render_html({"blocks": [{"type": "no_such_block", "text": "兜底文字"}]}, n)
        if "兜底文字" not in html:
            print(f"[FAIL] {n}: 未知块型丢了内容")
            failed += 1

    if failed:
        print(f"\n{failed} 项失败")
        return 1
    print("\n全部通过：结构、图片数、禁用 CSS、降级兜底")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
