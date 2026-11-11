"""主题令牌（design tokens）。

7 套主题 = 3 套通用审美 + 4 个生活场景包。
每套只写与 BASE 的差异，get_theme() 负责合并，新增一套主题通常只要十几行。

约束：微信公众号编辑器会剥离 <style>/<class>/<id>，主题只能通过
「内联样式 + 结构差异」表达，所以这里全部是可直接拼进 style 属性的字面值。
"""

FONT_SANS = (
    "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',"
    "'Microsoft YaHei',sans-serif"
)
FONT_SERIF = "'Songti SC','Noto Serif SC',Georgia,'Times New Roman',serif"
FONT_MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

# 所有主题共享的底座，未覆盖的键取这里的值
BASE = {
    "label": "",
    "group": "general",          # general | scene
    "scene": "",
    "font": FONT_SANS,
    "caption_font": FONT_SANS,
    "body_size": "16px",
    "body_color": "#38332c",
    "line_height": "1.85",
    "letter_spacing": "0.5px",
    "accent": "#b3552f",
    "accent_2": "#c9a46a",
    "accent_soft": "#f7efe9",
    "sub_color": "#8a8074",
    "rule": "#e6ded2",
    "rule_style": "solid",
    "radius": "4px",
    "radius_lg": "10px",
    "radius_pill": "20px",
    "numbered": False,
    "highlight": "#f6e3cf",
    "callout_bg": "#fbf7f2",
    "paper": "#ffffff",
    "card_bg": "#ffffff",
    "card_border": "#efe9e0",
    "chip_bg": "#ffffff",
    "chip_text": "#8a8074",
    "num_color": "#1f1d1a",
    "num_font": FONT_MONO,
    "shadow": "0 2px 10px rgba(0,0,0,0.10)",
    "gap": "22px",
    "pad": "0 2px",
    "supports": [],              # 该主题启用的专属块（空 = 仅通用块）
}

THEMES = {
    # ---------------------------------------------------------------- 通用
    "magazine": {
        "label": "杂志感",
        "font": FONT_SERIF,
        "caption_font": FONT_SANS,
        "body_color": "#38332c",
        "line_height": "1.9",
        "letter_spacing": "0.6px",
        "accent": "#b3552f",
        "accent_soft": "#f7efe9",
        "sub_color": "#8a8074",
        "rule": "#e6ded2",
        "numbered": True,
        "highlight": "#f6e3cf",
        "callout_bg": "#fbf7f2",
        "paper": "#fffdfa",
    },
    "minimal": {
        "label": "极简",
        "font": FONT_SANS,
        "body_color": "#2b2b2b",
        "line_height": "2",
        "letter_spacing": "0.4px",
        "accent": "#111111",
        "accent_soft": "#f5f5f5",
        "sub_color": "#9a9a9a",
        "rule": "#ececec",
        "radius": "2px",
        "highlight": "#f0f0f0",
        "callout_bg": "#fafafa",
        "pad": "0 6px",
    },
    "tech": {
        "label": "科技感",
        "body_size": "15.5px",
        "body_color": "#334155",
        "line_height": "1.8",
        "letter_spacing": "0.3px",
        "accent": "#0f172a",
        "accent_2": "#38bdf8",
        "accent_soft": "#f1f5f9",
        "sub_color": "#7c8ba1",
        "rule": "#e2e8f0",
        "radius": "8px",
        "numbered": True,
        "highlight": "#e0f2fe",
        "callout_bg": "#f1f5f9",
        "card_border": "#e2e8f0",
        "pad": "0 4px",
    },
    # ---------------------------------------------------------------- 生活场景
    "family": {
        "label": "家庭亲子",
        "group": "scene",
        "scene": "family",
        "body_size": "16px",
        "line_height": "2",
        "letter_spacing": "0.5px",
        "accent": "#e08a3c",
        "accent_2": "#c9a46a",
        "accent_soft": "#fbf1e6",
        "sub_color": "#9c8a76",
        "rule": "#f0ece4",
        "radius": "14px",
        "radius_lg": "18px",
        "radius_pill": "20px",
        "highlight": "#fde9cf",
        "callout_bg": "#fdf6ee",
        "paper": "#fffdf8",
        "card_border": "#f0ece4",
        "chip_bg": "#ffffff",
        "chip_text": "#9c8a76",
        "num_color": "#e08a3c",
        "gap": "24px",
        "supports": ["photo_polaroid", "kid_quote", "checklist", "dialogue"],
    },
    "travel": {
        "label": "旅行出门",
        "group": "scene",
        "scene": "travel",
        "body_size": "15.5px",
        "line_height": "1.85",
        "letter_spacing": "0.6px",
        "accent": "#35657e",
        "accent_2": "#c9a46a",
        "accent_soft": "#eaf2f5",
        "sub_color": "#7c8b92",
        "rule": "#e2e8f0",
        "radius": "8px",
        "radius_lg": "12px",
        "highlight": "#d8ebf2",
        "callout_bg": "#f2f7f9",
        "card_border": "#e2e8f0",
        "num_color": "#35657e",
        "gap": "20px",
        "supports": ["timeline", "route_table", "weather_card", "stamp"],
    },
    "daily": {
        "label": "日常随笔",
        "group": "scene",
        "scene": "daily",
        "font": FONT_SERIF,
        "caption_font": FONT_SANS,
        "body_size": "16px",
        "line_height": "2",
        "letter_spacing": "0.8px",
        "accent": "#4f6b5d",
        "accent_2": "#a8b8a8",
        "accent_soft": "#eef3ef",
        "sub_color": "#8a948c",
        "rule": "#e3e8e4",
        "radius": "4px",
        "highlight": "#e4ece6",
        "callout_bg": "#f7f9f7",
        "paper": "#fdfcfa",
        "card_border": "#e8ece8",
        "num_color": "#4f6b5d",
        "gap": "26px",
        "pad": "0 3px",
        "supports": ["drop_cap", "margin_note", "letter_paper", "sign_off"],
    },
    "anniversary": {
        "label": "纪念日时刻",
        "group": "scene",
        "scene": "anniversary",
        "font": FONT_SERIF,
        "caption_font": FONT_SANS,
        "body_size": "16px",
        "line_height": "2",
        "letter_spacing": "1.2px",
        "accent": "#8c2f39",
        "accent_2": "#c9a46a",
        "accent_soft": "#f6ecec",
        "sub_color": "#a08a8a",
        "rule": "#efe6e6",
        "radius": "2px",
        "radius_lg": "6px",
        "highlight": "#f5dede",
        "callout_bg": "#fbf4f4",
        "paper": "#fffcf9",
        "card_border": "#e6d2d2",
        "num_color": "#8c2f39",
        "gap": "28px",
        "supports": ["countdown_card", "ticket_stub", "compare_pair", "memory_band"],
    },
}

DEFAULT_THEME = "magazine"

# 场景 → 默认主题包，供 profile.typesetting.scene 使用
SCENE_TO_THEME = {
    "family": "family",
    "travel": "travel",
    "daily": "daily",
    "anniversary": "anniversary",
}

# 所有主题都支持的通用块
GENERIC_BLOCKS = [
    "h2", "h3", "lead", "p", "quote", "list", "callout",
    "image", "images", "code", "divider", "footer",
]


def get_theme(name: str | None) -> dict:
    key = (name or DEFAULT_THEME).strip().lower()
    if key not in THEMES:
        raise ValueError(
            f"未知主题 {name!r}，可选：{', '.join(THEMES)}"
        )
    t = dict(BASE)
    t.update(THEMES[key])
    t["key"] = key
    t["supports"] = list(t.get("supports") or [])
    return t


def theme_names() -> list[str]:
    return list(THEMES)


def blocks_for_theme(name: str | None) -> list[str]:
    """该主题可用的块白名单，用于约束 LLM 不要把不认识的结构塞进来。"""
    t = get_theme(name)
    return GENERIC_BLOCKS + t["supports"]
