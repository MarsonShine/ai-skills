"""Shared parsing for WeChat article block documents.

A document is either a JSON list of blocks or an object with a ``blocks``
key.  Blocks carry content only; colours and sizes live in ``themes.py``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

# Prose that is read as running text.  Captions, code and image attributes are
# deliberately excluded from voice analysis.
PROSE_FIELDS: dict[str, tuple[str, ...]] = {
    "lead": ("text",),
    "p": ("text",),
    "h2": ("text",),
    "h3": ("text",),
    "footer": ("text",),
    "quote": ("text", "source"),
    "list": (),
    "callout": ("title",),
    "kid_quote": ("text",),
    "margin_note": ("note", "text"),
    "letter_paper": ("text",),
    "drop_cap": ("text",),
    "memory_band": ("text",),
    "sign_off": (),
    "photo_polaroid": (),
}

ITEM_FIELDS = {"list", "callout", "checklist"}

# Blocks whose prose sits in a nested list.  The tuple is
# (list key, text key).
NESTED_FIELDS: dict[str, tuple[str, str]] = {
    "dialogue": ("lines", "text"),
    "timeline": ("items", "title"),
    "route_table": ("rows", "route"),
    "checklist": ("items", ""),
    "compare_pair": (),
}

IMAGE_BLOCKS = {"image", "photo_polaroid", "compare_pair"}

MARKUP = re.compile(r"\*\*|==|`|~~|<br\s*/?>", re.IGNORECASE)
SENTENCE = re.compile(r"[^。！？!?…\n]+[。！？!?…]+[”’」』）)]*|[^。！？!?…\n]+$")
QUOTED = re.compile(r"“[^”]*”|「[^」]*」|『[^』]*』|《[^》]*》")

CJK = re.compile(r"[\u3400-\u9fffA-Za-z0-9]")
DIGIT = re.compile(r"\d")


class DocumentError(ValueError):
    """Raised when the article document cannot be used."""


@dataclass(frozen=True)
class Sentence:
    block_index: int
    field: str
    index: int
    text: str
    start: int
    end: int
    quoted: bool

    @property
    def sentence_id(self) -> str:
        return f"{self.block_index}:{self.field}:{self.index}"


@dataclass(frozen=True)
class Unit:
    block_index: int
    field: str
    text: str
    quoted: bool
    block_type: str
    sentences: tuple[Sentence, ...]


def load_document(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise DocumentError(f"无法读取文章块文件：{error}") from error
    except json.JSONDecodeError as error:
        raise DocumentError(f"文章块不是合法 JSON：第 {error.lineno} 行第 {error.colno} 列") from error
    if isinstance(data, list):
        data = {"blocks": data}
    if not isinstance(data, dict):
        raise DocumentError("文章块应为 JSON 对象或数组")
    document = dict(data)
    blocks = document.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise DocumentError("blocks 应为非空数组")
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise DocumentError(f"第 {index} 个 block 应为对象")
        kind = block.get("type")
        if not isinstance(kind, str) or not kind.strip():
            raise DocumentError(f"第 {index} 个 block 缺少 type")
    for key in ("title", "author", "digest", "scene", "profile"):
        value = document.get(key)
        if value is not None and not isinstance(value, str):
            raise DocumentError(f"{key} 应为字符串")
    document["blocks"] = blocks
    return document


def clean_with_map(raw: str) -> tuple[str, list[int]]:
    """Remove light Markdown markers and map clean offsets back to raw."""
    clean: list[str] = []
    mapping: list[int] = []
    index = 0
    while index < len(raw):
        match = MARKUP.match(raw, index)
        if match:
            index = match.end()
            continue
        clean.append(raw[index])
        mapping.append(index)
        index += 1
    mapping.append(len(raw))
    return "".join(clean), mapping


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split cleaned prose into sentence spans.

    Terminal punctuation and a closing quote stay with the sentence.  A block
    boundary or newline always starts a new sentence.
    """
    spans: list[tuple[int, int, str]] = []
    for match in SENTENCE.finditer(text):
        start, end = match.span()
        piece = text[start:end]
        left = len(piece) - len(piece.lstrip())
        right = len(piece.rstrip())
        if right <= left:
            continue
        spans.append((start + left, start + right, piece[left:right]))
    return spans


def content_length(text: str) -> int:
    return len(CJK.findall(text))


def quoted_ranges(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in QUOTED.finditer(text)]


def inside(ranges: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start >= left and end <= right for left, right in ranges)


def _raw_span(mapping: list[int], start: int, end: int) -> tuple[int, int]:
    return mapping[start], mapping[end - 1] + 1 if end > start else mapping[start]


def _sentences(block_index: int, field: str, raw: str, quoted: bool) -> tuple[Sentence, ...]:
    clean, mapping = clean_with_map(raw)
    ranges = quoted_ranges(clean)
    result = []
    for index, (start, end, text) in enumerate(split_sentences(clean)):
        raw_start, raw_end = _raw_span(mapping, start, end)
        result.append(
            Sentence(
                block_index=block_index,
                field=field,
                index=index,
                text=text,
                start=raw_start,
                end=raw_end,
                quoted=quoted or inside(ranges, start, end),
            )
        )
    return tuple(result)


def _iter_unit_fields(block_index: int, block: dict[str, Any]) -> Iterator[tuple[str, str, bool, str]]:
    kind = str(block.get("type", ""))
    for field in PROSE_FIELDS.get(kind, ()):
        value = block.get(field)
        if isinstance(value, str) and value.strip():
            yield field, value, kind == "quote", kind
    if kind in ITEM_FIELDS:
        items = block.get("items")
        if isinstance(items, list):
            for index, item in enumerate(items):
                if isinstance(item, str) and item.strip():
                    yield f"items.{index}", item, kind == "callout", kind
    nested = NESTED_FIELDS.get(kind)
    if nested:
        key, text_key = nested
        values = block.get(key)
        if isinstance(values, list):
            for index, item in enumerate(values):
                if text_key == "" and isinstance(item, str) and item.strip():
                    yield f"{key}.{index}", item, False, kind
                elif isinstance(item, dict):
                    value = item.get(text_key)
                    if isinstance(value, str) and value.strip():
                        yield f"{key}.{index}.{text_key}", value, False, kind
    # A generic block may still carry a text field (for example a future
    # scene block); include it so the detector does not silently miss prose.
    if kind not in PROSE_FIELDS and kind not in ITEM_FIELDS and kind not in NESTED_FIELDS:
        value = block.get("text")
        if isinstance(value, str) and value.strip():
            yield "text", value, False, kind


def iter_units(blocks: list[dict[str, Any]]) -> list[Unit]:
    units: list[Unit] = []
    for block_index, block in enumerate(blocks):
        for field, raw, quoted, kind in _iter_unit_fields(block_index, block):
            units.append(
                Unit(
                    block_index=block_index,
                    field=field,
                    text=raw,
                    quoted=quoted,
                    block_type=kind,
                    sentences=_sentences(block_index, field, raw, quoted),
                )
            )
    return units


def sentences_of(units: list[Unit]) -> list[Sentence]:
    return [sentence for unit in units for sentence in unit.sentences]


def field_value(block: dict[str, Any], field: str) -> str:
    parts = field.split(".")
    value: Any = block
    for part in parts:
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise DocumentError(f"无法定位字段 {field}")
    if not isinstance(value, str):
        raise DocumentError(f"字段 {field} 不是文本")
    return value


def set_field_value(block: dict[str, Any], field: str, text: str) -> None:
    parts = field.split(".")
    value: Any = block
    for part in parts[:-1]:
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    last = parts[-1]
    if isinstance(value, list):
        value[int(last)] = text
    else:
        value[last] = text


def image_sources(document: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    cover = document.get("cover")
    if isinstance(cover, str) and cover:
        sources.append(cover)
    for block in document["blocks"]:
        kind = block.get("type")
        if kind in {"image", "photo_polaroid"}:
            value = block.get("src")
            if isinstance(value, str) and value and value not in sources:
                sources.append(value)
        elif kind == "compare_pair":
            for key in ("a", "b"):
                value = block.get(key)
                if isinstance(value, str) and value and value not in sources:
                    sources.append(value)
    return sources


def text_content(blocks: list[dict[str, Any]]) -> str:
    """Plain text used for character counts and detail density."""
    parts: list[str] = []
    for unit in iter_units(blocks):
        parts.extend(sentence.text for sentence in unit.sentences)
    return "\n".join(parts)
