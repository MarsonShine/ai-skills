"""Prepare local images for WeChat: four quality tiers and honest QC.

WeChat re-encodes on upload.  The only reliable definition of "lossless" is
pixel equality between the prepared file and the downloaded copy.  This module
therefore refuses to label a file lossless unless it really is.
"""

from __future__ import annotations

import hashlib
import io
import math
import os
import re
import warnings
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageChops, ImageOps, UnidentifiedImageError
except ImportError:  # pragma: no cover - exercised through article.py
    Image = None  # type: ignore[assignment]


LIMITS = {"body": 1 * 1024 * 1024, "cover": 10 * 1024 * 1024}
QUALITIES = ("lossless", "high", "balanced", "small")
TIER_DEFAULT_WIDTH = {"lossless": 29999, "high": 1280, "balanced": 1280, "small": 1080}
JPEG_MAX_HEIGHT = 16383
PNG_MAX_HEIGHT = 29999


class ImageError(ValueError):
    """Input image cannot be prepared."""


class LosslessError(ImageError):
    """The lossless tier cannot fit the upload limit without changing pixels."""

    def __init__(self, message: str, options: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.options = options or []


def _require_pillow() -> None:
    if Image is None:
        raise ImageError("缺少 Pillow，请先运行 python -m pip install Pillow")


def _format_size(width: int, height: int) -> str:
    return f"{width}x{height}"


def _encoded(image: "Image.Image", fmt: str, **options: Any) -> bytes:
    output = io.BytesIO()
    image.save(output, fmt, **options)
    return output.getvalue()


def _encode_png(image: "Image.Image") -> bytes:
    return _encoded(image, "PNG", optimize=True, compress_level=9)


def _encode_jpeg(image: "Image.Image", quality: int) -> bytes:
    # Pillow 12.3 can corrupt 4:2:2 output when optimize=True; keep 4:2:2
    # without optimization for high quality and use optimized 4:2:0 below 90.
    if quality >= 90:
        return _encoded(image, "JPEG", quality=quality, subsampling=1)
    return _encoded(image, "JPEG", quality=quality, optimize=True, subsampling=2)


def _fit(image: "Image.Image", max_width: int, max_height: int) -> "Image.Image":
    width, height = image.size
    scale = min(1.0, max_width / width, max_height / height)
    if scale >= 1:
        return image
    return image.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.Resampling.LANCZOS)


def _shrink(image: "Image.Image", ratio: float) -> "Image.Image":
    width, height = image.size
    return image.resize((max(1, round(width * ratio)), max(1, round(height * ratio))), Image.Resampling.LANCZOS)


def _pixel_equal(expected: "Image.Image", data: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(data)) as decoded:
            if decoded.size != expected.size:
                return False
            if decoded.mode != expected.mode:
                decoded = decoded.convert(expected.mode)
            difference = ImageChops.difference(decoded, expected)
            return all(high == 0 for _, high in difference.getextrema())
    except (OSError, ValueError):
        return False


def _jpeg_under_limit(image: "Image.Image", limit: int, start: int = 95, floor: int = 60) -> tuple[bytes, int]:
    """Return the highest JPEG quality that fits, resizing only if the floor fails."""
    working = image
    for _ in range(12):
        candidate = _encode_jpeg(working, start)
        if len(candidate) < limit:
            return candidate, start
        low, high = floor, start - 1
        best: tuple[bytes, int] | None = None
        while low <= high:
            middle = (low + high) // 2
            data = _encode_jpeg(working, middle)
            if len(data) < limit:
                best = (data, middle)
                low = middle + 1
            else:
                high = middle - 1
        if best is not None:
            return best
        ratio = min(0.92, math.sqrt(limit / len(candidate)) * 0.95)
        if ratio >= 0.999:
            ratio = 0.92
        working = _shrink(working, ratio)
    raise ImageError("无法在保持可读尺寸的前提下压到上传上限内。可换图或降低尺寸。")


def _png_under_limit(image: "Image.Image", limit: int) -> tuple[bytes, "Image.Image"]:
    working = image
    data = _encode_png(working)
    for _ in range(12):
        if len(data) < limit:
            return data, working
        ratio = min(0.92, math.sqrt(limit / len(data)) * 0.95)
        if ratio >= 0.999:
            ratio = 0.92
        working = _shrink(working, ratio)
        data = _encode_png(working)
    raise ImageError("无法把 PNG 压到上传上限内。可换图或选择 balanced。")


def _inspect(source: Path) -> tuple["Image.Image", dict[str, Any]]:
    _require_pillow()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with source.open("rb") as stream, Image.open(stream) as raw:
                if getattr(raw, "n_frames", 1) != 1:
                    raise ImageError("只支持单帧图片；请先选定要使用的一帧。")
                file_format = raw.format or ""
                src_px = raw.size
                src_bytes = os.fstat(stream.fileno()).st_size
                depth = 8
                if file_format == "PNG":
                    saved = stream.tell()
                    stream.seek(24)
                    depth = 16 if stream.read(1) == b"\x10" else 8
                    stream.seek(saved)
                if file_format not in {"PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF"}:
                    raise ImageError(f"不支持的图片格式：{file_format or '未知'}")
                oriented = ImageOps.exif_transpose(raw)
                alpha = "A" in oriented.getbands() or "transparency" in oriented.info
                color_reduced = oriented.mode not in {"1", "L", "LA", "P", "RGB", "RGBA"} or depth > 8
                image = oriented.convert("RGBA" if alpha else "RGB")
                image.info.clear()
    except UnidentifiedImageError as error:
        raise ImageError("无法解码图片，请先导出为可读的 JPEG、PNG 或 WebP。") from error
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ImageError("图片像素过多，已拒绝解码；请先缩小尺寸。") from error
    return image, {
        "src_px": _format_size(*src_px),
        "src_bytes": src_bytes,
        "input_format": file_format.lower(),
        "alpha": alpha,
        "depth": depth,
        "color_reduced": color_reduced,
    }


def _jpeg_fixed_quality(image: "Image.Image", limit: int, quality: int) -> tuple[bytes, "Image.Image"]:
    """Keep the quality fixed and reduce dimensions until the file fits."""
    working = image
    for _ in range(12):
        data = _encode_jpeg(working, quality)
        if len(data) < limit:
            return data, working
        ratio = min(0.92, math.sqrt(limit / len(data)) * 0.95)
        if ratio >= 0.999:
            ratio = 0.92
        working = _shrink(working, ratio)
    raise ImageError("维持质量不变时无法压到上传上限内，请换图或改用 balanced。")


def _lossless_options(image: "Image.Image", limit: int, current: int) -> list[dict[str, Any]]:
    width, height = image.size
    scale = min(0.98, math.sqrt(limit / max(1, current)) * 0.95)
    return [
        {
            "action": "resize",
            "size": _format_size(max(1, round(width * scale)), max(1, round(height * scale))),
            "note": "缩尺寸后仍是 PNG，但像素已变化，不再是严格无损",
        },
        {"action": "format", "format": "jpeg", "note": "换 JPG 可显著减小体积，但有损"},
        {"action": "quality", "quality": "balanced", "note": "自动找最高可用质量并明确报告降了什么"},
    ]


def prepare(
    source: str | Path,
    out_dir: str | Path,
    stem: str,
    quality: str = "balanced",
    role: str = "body",
    max_width: int | None = None,
    max_height: int | None = None,
) -> dict[str, Any]:
    if quality not in QUALITIES:
        raise ImageError("画质可选 lossless、high、balanced、small")
    if role not in LIMITS:
        raise ImageError("role 可选 body 或 cover")
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9._-]{0,99}", stem):
        raise ImageError("图片标识须为 1–100 个字母、数字、点、连字符或下划线。")
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise ImageError(f"找不到图片：{path}")
    image, info = _inspect(path)
    limit = LIMITS[role]
    src_px = info["src_px"]
    src_bytes = info["src_bytes"]
    alpha = info["alpha"]
    if quality == "lossless" and info["color_reduced"]:
        raise LosslessError("严格无损只支持 8 位 RGB、灰度、索引色或带透明通道的图片；请先转换色彩格式。")
    if max_width is None:
        max_width = TIER_DEFAULT_WIDTH[quality]
    if max_height is None:
        max_height = JPEG_MAX_HEIGHT if not alpha else PNG_MAX_HEIGHT
    if max_width <= 0 or max_height <= 0:
        raise ImageError("max_width 和 max_height 必须为正整数。")

    resized = False
    reason: str | None = None
    fmt = "png" if alpha or quality == "lossless" else "jpeg"
    if quality == "lossless":
        if image.height > PNG_MAX_HEIGHT:
            raise LosslessError(f"图片高度 {image.height}px 超过微信 PNG 上限 {PNG_MAX_HEIGHT}px，上传会失败。")
        if info["input_format"] == "jpeg" and not alpha and not info["color_reduced"]:
            if image.height > JPEG_MAX_HEIGHT:
                raise LosslessError(
                    f"图片高度 {image.height}px 超过微信 JPEG 上限 {JPEG_MAX_HEIGHT}px；"
                    "lossless 档不缩尺寸，请换图或改用 balanced。"
                )
            # A JPEG cannot be made lossless.  Keep its quality and dimensions,
            # and report that it remains lossy instead of pretending otherwise.
            data = _encode_jpeg(image, 95)
            if len(data) >= limit:
                raise LosslessError(
                    f"lossless 档不缩尺寸、不降质量，但该 JPEG 重新编码后为 {len(data)} 字节，"
                    f"超过 {role} 上限 {limit} 字节。请换 PNG、缩尺寸或改用 balanced。",
                    [
                        {"action": "resize", "note": "缩尺寸会有损，且这张图本身已是 JPEG"},
                        {"action": "quality", "quality": "balanced", "note": "自动缩到能上传的尺寸并报告"},
                    ],
                )
            fmt = "jpeg"
            output = image
            reason = "JPEG 源图本身有损；lossless 档不缩尺寸、不降质量，但微信仍会二次编码，因此不能标记为无损"
            if image.width > 1280:
                reason += "；源图宽度超过 1280px，微信可能缩放"
        else:
            data = _encode_png(image)
            if len(data) >= limit:
                raise LosslessError(
                    f"无损 PNG 为 {len(data)} 字节，超过 {role} 上限 {limit} 字节；"
                    "请缩尺寸、换 JPG 或改用 --quality balanced（会明确报告降了什么）。",
                    _lossless_options(image, limit, len(data)),
                )
            fmt = "png"
            output = image
    elif quality == "high":
        working = _fit(image, max_width, max_height)
        if alpha:
            data, output = _png_under_limit(working, limit)
            fmt = "png"
        elif info["input_format"] in {"png", "webp", "gif", "bmp", "tiff"}:
            png_data = _encode_png(working)
            if len(png_data) < limit:
                data = png_data
                output = working
                fmt = "png"
            else:
                data, output = _jpeg_fixed_quality(working, limit, 92)
                fmt = "jpeg"
        else:
            data, output = _jpeg_fixed_quality(working, limit, 92)
            fmt = "jpeg"
        reason = "high 档只在必要时缩尺寸，JPEG 质量锁 92；上传后仍可能被微信二次编码"
    elif quality == "small":
        working = _fit(image, max_width, max_height)
        if alpha:
            data, output = _png_under_limit(working, limit)
            fmt = "png"
        else:
            data = _encode_jpeg(working, 80)
            if len(data) >= limit:
                low, high = 55, 79
                best = None
                while low <= high:
                    middle = (low + high) // 2
                    candidate = _encode_jpeg(working, middle)
                    if len(candidate) < limit:
                        best = (candidate, middle)
                        low = middle + 1
                    else:
                        high = middle - 1
                if best:
                    data = best[0]
                else:
                    data, _ = _png_under_limit(working, limit)
                    fmt = "png"
            output = working
        reason = "small 档为省流量主动降尺寸与质量"
    else:  # balanced
        working = _fit(image, max_width, max_height)
        if alpha:
            data, output = _png_under_limit(working, limit)
            fmt = "png"
            reason = "透明图保持 PNG；尺寸按需缩小"
        else:
            png_data = _encode_png(working)
            if len(png_data) < limit and info["input_format"] in {"png", "webp", "gif", "bmp", "tiff"}:
                data = png_data
                output = working
                fmt = "png"
            else:
                data, used_quality = _jpeg_under_limit(working, limit, start=95, floor=60)
                output = working
                fmt = "jpeg"
                reason = f"balanced 档先定尺寸，再用二分找到可用最高 JPEG 质量（实际 {used_quality}）"
    resized = output.size != image.size

    if fmt == "png" and output.height > PNG_MAX_HEIGHT:
        raise ImageError("图片高度超过微信 PNG 上限。")
    if fmt == "jpeg" and output.height > JPEG_MAX_HEIGHT:
        raise ImageError("图片高度超过微信 JPEG 上限。")

    pixel_equal = _pixel_equal(image, data)
    lossless = quality == "lossless" and fmt == "png" and pixel_equal and not resized
    if quality == "lossless" and fmt == "png" and not lossless:
        raise LosslessError("本地解码像素校验失败，未输出图片。")
    if quality != "lossless" and pixel_equal and not resized:
        reason = None if fmt == "png" else "尺寸未变，但 JPEG 编码仍会改变像素"

    target_dir = Path(out_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = "png" if fmt == "png" else "jpg"
    target = target_dir / f"{stem}.{suffix}"
    if target.resolve() == path:
        raise ImageError("输出路径与原图相同，请指定独立的工作目录。")
    temporary = target.with_name(target.name + ".tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)

    if not reason and quality != "lossless" and not pixel_equal:
        reason = f"{quality} 档有损处理，尺寸或质量至少一项发生变化"
    return {
        "ok": True,
        "path": str(target),
        "role": role,
        "quality": quality,
        "src_px": src_px,
        "output_px": _format_size(*output.size),
        "src_bytes": src_bytes,
        "output_bytes": len(data),
        "format": "png" if fmt == "png" else "jpeg",
        "pixel_equal": pixel_equal,
        "lossless": lossless,
        "resized": resized,
        "reencoded": not (quality == "lossless" and fmt == "png" and pixel_equal and not resized),
        "reason": reason,
        "sha256": hashlib.sha256(data).hexdigest(),
        "limit": limit,
        "options": [],
    }


def verify(expected: str | Path, downloaded: str | Path) -> dict[str, Any]:
    """Compare a prepared local file with the copy downloaded from the CDN."""
    _require_pillow()
    left = Path(expected).expanduser().resolve()
    right = Path(downloaded).expanduser().resolve()
    try:
        with Image.open(left) as first, Image.open(right) as second:
            first_image = first.convert("RGBA" if "A" in first.getbands() else "RGB")
            second_image = second.convert(first_image.mode)
            equal = first_image.size == second_image.size and all(
                high == 0 for _, high in ImageChops.difference(first_image, second_image).getextrema()
            )
            return {
                "ok": True,
                "expected_px": _format_size(*first.size),
                "remote_px": _format_size(*second.size),
                "expected_bytes": left.stat().st_size,
                "remote_bytes": right.stat().st_size,
                "pixel_equal": equal,
                "lossless": equal and first.size == second.size,
                "reason": None if equal else "远端图片被缩放或重新编码",
            }
    except (OSError, ValueError) as error:
        return {
            "ok": False,
            "error": f"无法比较图片：{error}",
            "expected_px": None,
            "remote_px": None,
            "pixel_equal": False,
            "lossless": False,
        }


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)\s*[xX×]\s*(\d+)", value.strip())
    if not match:
        raise ImageError("尺寸格式应为 宽x高，例如 1080x720")
    return int(match.group(1)), int(match.group(2))
