"""Prepare a still image without camera or location metadata for a WeChat article or cover."""

import argparse
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageCms, ImageOps, UnidentifiedImageError
except ImportError:
    print(json.dumps({"ok": False, "code": 2, "error": "Install Pillow in the Python environment used by this skill."}))
    raise SystemExit(2)


LIMITS = {"body": 1024 * 1024, "cover": 10 * 1024 * 1024}
END_OF_JPEG_SCAN = re.compile(rb"\xff+[^\x00\xd0-\xd7\xff]")


class LosslessError(ValueError):
    pass


def plain_jpeg(data):
    """Allow baseline/progressive coding segments and thumbnail-free JFIF only."""
    if not data.startswith(b"\xff\xd8"):
        return False
    pos = 2
    while pos < len(data) and data[pos] == 0xFF:
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            return False
        marker = data[pos]
        pos += 1
        if marker == 0xD9:
            return pos == len(data)  # Reject trailers, including embedded previews.
        size = int.from_bytes(data[pos:pos + 2], "big")
        if size < 2 or pos + size > len(data):
            return False
        if marker == 0xE0:
            if size != 16 or data[pos + 2:pos + 7] != b"JFIF\x00" or data[pos + 14:pos + 16] != b"\x00\x00":
                return False
        elif marker not in {0xC0, 0xC2, 0xC4, 0xDA, 0xDB, 0xDD}:
            return False
        pos += size
        if marker == 0xDA:
            # Between scans FF00 is a stuffed byte and FFD0..D7 are restart markers.
            end = END_OF_JPEG_SCAN.search(data, pos)
            if not end:
                return False
            pos = end.start()
    return False


def encoded(image, fmt, **options):
    output = io.BytesIO()
    image.save(output, fmt, icc_profile=image.info.get("icc_profile"), **options)
    return output.getvalue()


def smaller(image, size, limit):
    ratio = min(0.90, math.sqrt(limit / size) * 0.93)
    dimensions = tuple(max(1, int(side * ratio)) for side in image.size)
    if dimensions == image.size:
        raise ValueError("保留色彩配置后仍超过上传限制，请先导出为标准 sRGB。")
    return image.resize(dimensions, Image.Resampling.LANCZOS)


def jpeg_under_limit(image, limit):
    while True:
        best = encoded(image, "JPEG", quality=92, optimize=True)
        if len(best) < limit:
            return best
        best = encoded(image, "JPEG", quality=72, optimize=True)
        if len(best) >= limit:
            image = smaller(image, len(best), limit)
            continue
        # At these dimensions retain the highest fitting quality from 72..91.
        low, high = 73, 91
        while low <= high:
            mid = (low + high) // 2
            candidate = encoded(image, "JPEG", quality=mid, optimize=True)
            if len(candidate) < limit:
                best = candidate
                low = mid + 1
            else:
                high = mid - 1
        return best


def prepare_image(source: Path, out_dir: Path, stem: str, quality: str, role: str):
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9._-]{0,99}", stem):
        raise ValueError("图片标识须为 1–100 个字母、数字、点、连字符或下划线。")
    limit = LIMITS[role]
    reusable = None
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with source.open("rb") as stream, Image.open(stream) as raw:
            if getattr(raw, "n_frames", 1) != 1:
                raise ValueError("只支持单帧图片；请先选定要使用的一帧。")
            file_format = raw.format
            src_px = raw.size
            src_bytes = os.fstat(stream.fileno()).st_size
            if file_format == "JPEG" and src_bytes < limit and raw.mode in {"RGB", "L"}:
                saved_offset = stream.tell()
                stream.seek(0)
                candidate = stream.read(limit)
                stream.seek(saved_offset)
                if len(candidate) < limit and plain_jpeg(candidate):
                    reusable = candidate
            color_reduced = raw.mode not in {"1", "L", "LA", "P", "RGB", "RGBA"}
            if raw.format == "PNG":
                # Pillow decodes 16-bit RGB PNG as 8-bit RGB. Inspect IHDR before labeling it lossless.
                saved_offset = stream.tell()
                stream.seek(24)
                color_reduced |= stream.read(1) == b"\x10"
                stream.seek(saved_offset)
            if quality == "lossless" and color_reduced:
                raise LosslessError("严格无损支持 8 位及以下的 RGB、灰度和索引色图片；请转换色彩格式或选择 balanced。")
            oriented = ImageOps.exif_transpose(raw)
            transparent = "A" in oriented.getbands() or "transparency" in oriented.info
            pixels = oriented.convert("RGBA" if transparent else "RGB")
            icc = oriented.info.get("icc_profile")
            # Pillow can implicitly re-emit metadata from Image.info when encoding PNG.
            pixels.info.clear()
            if icc:
                try:
                    profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                    if profile.profile.xcolor_space.strip() == "RGB" and oriented.mode in {"P", "RGB", "RGBA"}:
                        pixels.info["icc_profile"] = icc
                    elif quality == "lossless":
                        raise LosslessError("无法将此色彩配置无损保留在输出的 RGB 图片中。")
                    else:
                        source_mode = "L" if "L" in oriented.getbands() else oriented.mode
                        srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
                        converted = ImageCms.profileToProfile(oriented.convert(source_mode), profile, srgb, outputMode="RGB")
                        if transparent:
                            converted.putalpha(pixels.getchannel("A"))
                        pixels = converted
                        pixels.info.clear()
                        color_reduced = True
                except (OSError, ImageCms.PyCMSError) as error:
                    raise ValueError("图片的 ICC 色彩配置无效，请先导出为 sRGB。") from error

    if reusable is not None:
        fmt, data = "jpg", reusable
    elif quality == "lossless" or file_format == "PNG" or transparent:
        fmt = "png"
        data = encoded(pixels, "PNG", optimize=True)
        if len(data) >= limit and quality == "lossless":
            raise LosslessError(f"去元数据并转正后的无损 PNG 为 {len(data)} 字节，须小于 {limit} 字节；可换图或选择 balanced。")
        if len(data) >= limit and transparent:
            working = pixels
            while len(data) >= limit:
                working = smaller(working, len(data), limit)
                data = encoded(working, "PNG", optimize=True)
        elif len(data) >= limit:
            fmt = "jpg"
            data = jpeg_under_limit(pixels, limit)
    else:
        fmt = "jpg"
        data = jpeg_under_limit(pixels, limit)

    with Image.open(io.BytesIO(data)) as decoded:
        output_px = decoded.size
        equal = False
        if not color_reduced and output_px == pixels.size:
            difference = ImageChops.difference(decoded.convert(pixels.mode), pixels)
            equal = all(high == 0 for _, high in difference.getextrema())
    if quality == "lossless" and not equal:
        raise LosslessError("本地解码像素校验失败，未输出图片。")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = (out_dir / f"{stem}.{fmt}").absolute()
    if path.resolve() == source.resolve():
        raise ValueError("输出路径与原图相同，请指定独立的工作目录。")
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=out_dir, delete=False) as handle:
            tmp = Path(handle.name)
            handle.write(data)
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return {
        "ok": True, "path": str(path), "role": role, "src_px": src_px,
        "oriented_px": pixels.size, "output_px": output_px, "src_bytes": src_bytes,
        "output_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "pixel_equal": equal, "remote_pixel_equal": None,
    }


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--quality", required=True, choices=("balanced", "lossless"))
    parser.add_argument("--role", required=True, choices=("body", "cover"))
    try:
        args = parser.parse_args()
        result = prepare_image(args.input, args.out_dir, args.stem, args.quality, args.role)
    except LosslessError as error:
        result = {"ok": False, "code": 7, "error": str(error)}
    except UnidentifiedImageError:
        result = {"ok": False, "code": 2, "error": "无法解码图片，请先导出为可读的 JPEG 或 PNG。"}
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        result = {"ok": False, "code": 2, "error": str(error)}
    print(json.dumps(result, ensure_ascii=True))
    return result.get("code", 0)


if __name__ == "__main__":
    sys.exit(main())
