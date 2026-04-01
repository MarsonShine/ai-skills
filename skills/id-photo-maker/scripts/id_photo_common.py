#!/usr/bin/env python3

from __future__ import annotations

import base64
import json
import mimetypes
import re
import urllib.parse
import urllib.request
from pathlib import Path

SIZE_PRESETS = {
    "1-inch": {
        "aliases": ["1-inch", "1 inch", "1寸", "一寸", "1in"],
        "width_mm": 25.0,
        "height_mm": 35.0,
        "label": "1-inch",
    },
    "2-inch": {
        "aliases": ["2-inch", "2 inch", "2寸", "二寸", "2in"],
        "width_mm": 35.0,
        "height_mm": 49.0,
        "label": "2-inch",
    },
    "small-1-inch": {
        "aliases": ["small-1-inch", "small 1 inch", "小一寸", "小1寸"],
        "width_mm": 22.0,
        "height_mm": 32.0,
        "label": "small-1-inch",
    },
    "passport": {
        "aliases": ["passport", "护照", "passport-photo"],
        "width_mm": 33.0,
        "height_mm": 48.0,
        "label": "passport",
    },
}

PAGE_PRESETS = {
    "a4": {
        "aliases": ["a4", "A4"],
        "width_mm": 210.0,
        "height_mm": 297.0,
        "margin_mm": 5.0,
        "gap_mm": 2.5,
        "page_css": "A4 portrait",
        "label": "A4",
    },
    "6inch": {
        "aliases": ["6inch", "6-inch", "6 inch", "6寸", "6in"],
        "width_mm": 152.0,
        "height_mm": 102.0,
        "margin_mm": 4.0,
        "gap_mm": 2.0,
        "page_css": "152mm 102mm",
        "label": "6-inch",
    },
}

BACKGROUND_PRESETS = {
    "white": "#FFFFFF",
    "blue": "#438EDB",
    "red": "#D94B52",
}

FRAMING_PRESETS = {
    "standard": {
        "aliases": ["standard", "headshot", "证件照", "standard-headshot"],
        "subject_height_ratio": 0.82,
        "top_margin_ratio": 0.08,
        "label": "standard",
    },
    "half-body": {
        "aliases": ["half-body", "half body", "半身照", "半身"],
        "subject_height_ratio": 0.90,
        "top_margin_ratio": 0.04,
        "label": "half-body",
    },
    "full-body": {
        "aliases": ["full-body", "full body", "全身照", "全身"],
        "subject_height_ratio": 0.96,
        "top_margin_ratio": 0.02,
        "label": "full-body",
    },
}

USER_AGENT = "CopilotCLI/id-photo-maker 1.0"


def normalize_token(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().lower())


def mm_to_px(mm_value: float, dpi: int = 300) -> int:
    return max(1, round(mm_value / 25.4 * dpi))


def px_to_mm(px_value: int, dpi: int = 300) -> float:
    return px_value / dpi * 25.4


def ensure_directory(path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: str | Path, payload: object) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def guess_extension_from_url(url: str, content_type: str | None = None) -> str:
    path_suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if path_suffix:
        return path_suffix
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            return guessed
    return ".png"


def download_file(url: str, destination: str | Path, timeout: float = 60.0) -> Path:
    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/*,*/*;q=0.8",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
        if not payload:
            raise RuntimeError(f"Downloaded file is empty: {url}")

        if not target.suffix:
            target = target.with_suffix(
                guess_extension_from_url(url, response.headers.get_content_type())
            )

        target.write_bytes(payload)
        return target


def file_to_data_uri(path: str | Path) -> str:
    target = Path(path).expanduser().resolve()
    mime_type, _ = mimetypes.guess_type(str(target))
    mime_type = mime_type or "application/octet-stream"
    encoded = base64.b64encode(target.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_alias_map(source: dict[str, dict]) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for key, spec in source.items():
        alias_map[normalize_token(key)] = key
        for alias in spec["aliases"]:
            alias_map[normalize_token(alias)] = key
    return alias_map


SIZE_ALIAS_MAP = _build_alias_map(SIZE_PRESETS)
PAGE_ALIAS_MAP = _build_alias_map(PAGE_PRESETS)
FRAMING_ALIAS_MAP = _build_alias_map(FRAMING_PRESETS)


def resolve_size_spec(size_value: str, dpi: int = 300) -> dict[str, float | int | str]:
    normalized = normalize_token(size_value)
    preset_key = SIZE_ALIAS_MAP.get(normalized)
    if preset_key:
        preset = SIZE_PRESETS[preset_key]
        return {
            "key": preset_key,
            "label": preset["label"],
            "width_mm": preset["width_mm"],
            "height_mm": preset["height_mm"],
            "width_px": mm_to_px(preset["width_mm"], dpi),
            "height_px": mm_to_px(preset["height_mm"], dpi),
            "dpi": dpi,
            "source": "preset",
        }

    mm_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm", size_value.strip(), re.I)
    if mm_match:
        width_mm = float(mm_match.group(1))
        height_mm = float(mm_match.group(2))
        return {
            "key": "custom-mm",
            "label": f"{width_mm:g}x{height_mm:g}mm",
            "width_mm": width_mm,
            "height_mm": height_mm,
            "width_px": mm_to_px(width_mm, dpi),
            "height_px": mm_to_px(height_mm, dpi),
            "dpi": dpi,
            "source": "custom-mm",
        }

    px_match = re.fullmatch(r"(\d+)\s*[x×]\s*(\d+)\s*px", size_value.strip(), re.I)
    if px_match:
        width_px = int(px_match.group(1))
        height_px = int(px_match.group(2))
        return {
            "key": "custom-px",
            "label": f"{width_px}x{height_px}px",
            "width_mm": px_to_mm(width_px, dpi),
            "height_mm": px_to_mm(height_px, dpi),
            "width_px": width_px,
            "height_px": height_px,
            "dpi": dpi,
            "source": "custom-px",
        }

    raise ValueError(
        "Unsupported size. Use a known preset like '1寸' or '2寸', "
        "or a custom value like '35x45mm' / '413x579px'."
    )


def resolve_page_preset(page_value: str) -> dict[str, float | str]:
    normalized = normalize_token(page_value)
    preset_key = PAGE_ALIAS_MAP.get(normalized)
    if not preset_key:
        raise ValueError(f"Unsupported page preset: {page_value}")
    preset = PAGE_PRESETS[preset_key]
    return {
        "key": preset_key,
        "label": preset["label"],
        "width_mm": preset["width_mm"],
        "height_mm": preset["height_mm"],
        "margin_mm": preset["margin_mm"],
        "gap_mm": preset["gap_mm"],
        "page_css": preset["page_css"],
    }


def resolve_framing(value: str) -> dict[str, float | str]:
    normalized = normalize_token(value)
    preset_key = FRAMING_ALIAS_MAP.get(normalized)
    if not preset_key:
        raise ValueError(
            "Unsupported framing. Use 'standard', 'half-body', or 'full-body'."
        )
    preset = FRAMING_PRESETS[preset_key]
    return {
        "key": preset_key,
        "label": preset["label"],
        "subject_height_ratio": preset["subject_height_ratio"],
        "top_margin_ratio": preset["top_margin_ratio"],
    }


def parse_color(value: str) -> tuple[tuple[int, int, int], str]:
    cleaned = value.strip().lower()
    if cleaned in BACKGROUND_PRESETS:
        cleaned = BACKGROUND_PRESETS[cleaned]

    hex_match = re.fullmatch(r"#?([0-9a-f]{6})", cleaned, re.I)
    if hex_match:
        raw = hex_match.group(1)
        rgb = tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))
        return rgb, f"#{raw.upper()}"

    rgb_match = re.fullmatch(
        r"(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})",
        cleaned,
    )
    if rgb_match:
        rgb = tuple(max(0, min(255, int(part))) for part in rgb_match.groups())
        return rgb, "#{:02X}{:02X}{:02X}".format(*rgb)

    raise ValueError(
        "Unsupported background color. Use white, blue, red, #RRGGBB, or R,G,B."
    )
