"""Scene tokens for personal WeChat articles.

Only tokens live here.  ``render.py`` combines them with semantic blocks; no
colour, width or font size is ever read from article data.
"""

from __future__ import annotations

from typing import Any

THEMES: dict[str, dict[str, Any]] = {
    "family": {
        "label": "家庭亲子",
        "accent": "#E08A3C",
        "accent_soft": "#FBF1E6",
        "paper": "#FFFDF8",
        "text": "#38332C",
        "sub": "#9C8A76",
        "rule": "#F0ECE4",
        "font": "'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif",
        "serif": False,
        "body": 16,
        "line": 2.0,
        "tracking": "0.5px",
        "radius": 14,
        "radius_pill": 20,
        "chip_bg": "#FFFFFF",
        "chip_text": "#9C8A76",
        "shadow": "0 2px 10px rgba(0,0,0,0.10)",
        "card_border": "1px solid #F0ECE4",
        "gap": 24,
        "supports": ["photo_polaroid", "kid_quote", "checklist", "dialogue"],
    },
    "travel": {
        "label": "旅行出门",
        "accent": "#35657E",
        "accent_soft": "#EAF2F5",
        "paper": "#FDFEFF",
        "text": "#334155",
        "sub": "#7C8B92",
        "rule": "#E2E8F0",
        "font": "'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif",
        "serif": False,
        "body": 15.5,
        "line": 1.85,
        "tracking": "0.6px",
        "radius": 8,
        "radius_pill": 16,
        "chip_bg": "#FFFFFF",
        "chip_text": "#7C8B92",
        "shadow": "0 2px 8px rgba(0,0,0,0.08)",
        "card_border": "1px solid #E2E8F0",
        "gap": 20,
        "supports": ["timeline", "route_table", "weather_card", "stamp"],
    },
    "daily": {
        "label": "日常随笔",
        "accent": "#4F6B5D",
        "accent_soft": "#EEF3EF",
        "paper": "#FDFCFA",
        "text": "#3A3A35",
        "sub": "#8A948C",
        "rule": "#E3E8E4",
        "font": "Georgia, 'Songti SC', 'SimSun', serif",
        "serif": True,
        "body": 16,
        "line": 2.0,
        "tracking": "0.8px",
        "radius": 4,
        "radius_pill": 14,
        "chip_bg": "#FFFFFF",
        "chip_text": "#8A948C",
        "shadow": "0 2px 8px rgba(0,0,0,0.07)",
        "card_border": "1px solid #E3E8E4",
        "gap": 26,
        "supports": ["drop_cap", "margin_note", "letter_paper", "sign_off"],
    },
    "anniversary": {
        "label": "纪念日时刻",
        "accent": "#8C2F39",
        "accent_soft": "#F6ECEC",
        "paper": "#FFFCF9",
        "text": "#3B2F2F",
        "sub": "#A08A8A",
        "rule": "#EFE6E6",
        "font": "Georgia, 'Songti SC', 'SimSun', serif",
        "serif": True,
        "body": 16,
        "line": 2.0,
        "tracking": "1.2px",
        "radius": 2,
        "radius_pill": 12,
        "chip_bg": "#FFFFFF",
        "chip_text": "#A08A8A",
        "shadow": "0 2px 10px rgba(0,0,0,0.08)",
        "card_border": "1px solid #EFE6E6",
        "gap": 26,
        "supports": ["countdown_card", "ticket_stub", "compare_pair", "memory_band"],
    },
}

SCENES = tuple(THEMES)
DEFAULT_SCENE = "daily"

# Blocks that belong to one scene's skin.  They still render in other scenes;
# the renderer only notes that the generic skin was used.
SCENE_BLOCKS = {scene: set(theme["supports"]) for scene, theme in THEMES.items()}


def theme_for(scene: str | None) -> dict[str, Any]:
    if not scene or scene == "auto":
        scene = DEFAULT_SCENE
    if scene not in THEMES:
        raise ValueError("场景可选 " + "、".join(SCENES))
    return THEMES[scene]
