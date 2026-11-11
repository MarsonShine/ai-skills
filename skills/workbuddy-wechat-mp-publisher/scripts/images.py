"""图片预处理：四档质量 + 无损判定 + 远端回读核验。

先说清楚一件事：微信会在入库时重新编码，任何客户端都无法绕过。
所谓「无损上传」不是骗服务端，而是把输入送进它不做有损处理的区间：

  PNG（高 ≤29999px）→ 尺寸与画质保留，透明通道不会被转 JPEG，实测无损
  JPEG（宽 ≤1280）  → 尺寸不变，但仍有二次质量压缩，有损
  JPEG（超尺寸）    → 等比缩小
  高 >29999px       → 上传直接失败

所以截图、图表、设计稿用 PNG 是「真无损」；摄影照片做不到。
真正的瓶颈是正文图 1MB 上限，不是压缩算法。

顺序铁律：**先定尺寸 → 再定格式 → 最后才谈质量**。
顺序错了，细节在第一步就丢了，这是「压完还是糊」的最常见原因。
"""

from __future__ import annotations

import hashlib
import io
import shutil
from pathlib import Path

from PIL import Image

BODY_LIMIT = 1_048_576       # media/uploadimg 单图上限 1MB
COVER_LIMIT = 10_485_760     # material/add_material 上限 10MB
PNG_MAX_H = 29999            # 超过直接上传失败
JPEG_MAX_H = 16383
JPEG_MAX_W = 1280            # 有损区间；不写死为硬阈值，只作目标宽

QUALITIES = ("lossless", "high", "balanced", "small")


def _fmt_bytes(n: int) -> str:
    return f"{n / 1024:.0f}K" if n < 1024 * 1024 else f"{n / 1048576:.1f}M"


def inspect(path: str | Path) -> dict:
    p = Path(path)
    with Image.open(p) as im:
        w, h = im.size
        return {
            "src": str(p),
            "format": (im.format or "").upper(),
            "mode": im.mode,
            "px": f"{w}x{h}",
            "width": w,
            "height": h,
            "bytes": p.stat().st_size,
            "has_alpha": im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info),
        }


def _encode(im: Image.Image, fmt: str, quality: int | None) -> bytes:
    buf = io.BytesIO()
    if fmt == "PNG":
        im.save(buf, "PNG", optimize=True, compress_level=9)
    else:
        im.convert("RGB").save(buf, "JPEG", quality=quality or 90, optimize=True, progressive=True)
    return buf.getvalue()


def _png_lossless_shrink(data: bytes) -> tuple[bytes, str] | None:
    """PNG 无损瘦身：优先 pngquant（若装了），否则只在调色板 ≤256 色时量化。"""
    if shutil.which("pngquant"):
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(data)
            src = f.name
        dst = src.replace(".png", "-q.png")
        try:
            subprocess.run(
                ["pngquant", "--force", "--quality", "100", "--speed", "1", src, "--output", dst],
                check=True, capture_output=True, timeout=60,
            )
            return Path(dst).read_bytes(), "pngquant 无损量化"
        except Exception:
            return None
        finally:
            Path(src).unlink(missing_ok=True)
            Path(dst).unlink(missing_ok=True)

    im = Image.open(io.BytesIO(data))
    colors = im.convert("RGBA").getcolors(maxcolors=257)
    if colors and len(colors) <= 256:
        shrunk = _encode(im.convert("P", palette=Image.ADAPTIVE, colors=256), "PNG", None)
        if len(shrunk) < len(data):
            return shrunk, "调色板量化（≤256 色，无损）"
    return None


def prepare(path: str | Path, quality: str = "balanced", out_dir: str | Path | None = None,
            limit: int = BODY_LIMIT) -> dict:
    """按档位产出可上传的图片。不写文件时返回 plan；超限且不允许降质则 ok=False。

    返回字段里的 lossless 是「本地这一步有没有损」，不代表服务端结果；
    服务端结果由 verify_remote 回读判定。
    """
    quality = quality if quality in QUALITIES else "balanced"
    info = inspect(path)
    src = Path(info["src"])
    out_dir = Path(out_dir) if out_dir else src.parent / ".wechat-mp"
    out_dir.mkdir(parents=True, exist_ok=True)

    w, h = info["width"], info["height"]
    fmt = info["format"] or "JPEG"
    result = {
        "src": str(src),
        "src_px": info["px"],
        "src_bytes": info["bytes"],
        "src_bytes_text": _fmt_bytes(info["bytes"]),
        "format_in": fmt,
        "quality": quality,
        "lossless": True,
        "action": "keep",
        "out": str(src),
        "out_px": info["px"],
        "out_bytes": info["bytes"],
        "reason": "",
        "ok": True,
    }

    # 高度硬上限：任何档位都救不了，只能缩
    if (fmt == "PNG" and h > PNG_MAX_H) or (fmt != "PNG" and h > JPEG_MAX_H):
        cap = PNG_MAX_H if fmt == "PNG" else JPEG_MAX_H
        result.update(ok=False, action="reject", lossless=False,
                      reason=f"高 {h}px 超过微信上限 {cap}px，必须缩小尺寸才能上传")

    # ---------- lossless：不缩、不降质
    if quality == "lossless" and result["ok"]:
        if info["bytes"] <= limit:
            return result
        data = src.read_bytes()
        if fmt == "PNG":
            shrunk = _png_lossless_shrink(data)
            if shrunk and len(shrunk[0]) <= limit:
                out = out_dir / f"{_stem(src)}.png"
                out.write_bytes(shrunk[0])
                return _finish(result, out, shrunk[1], lossless=True)
            result.update(
                ok=False, action="blocked", lossless=False,
                reason=(
                    f"PNG 原图 {_fmt_bytes(info['bytes'])} 超过 1MB，且无进一步无损压缩空间。"
                    "请从三选一：①缩到 1280 宽（会降尺寸）②改 high 档（会重编码）③换小图"
                ),
            )
            return result
        # JPEG 无法在不损失画质的前提下变小
        result.update(
            ok=False, action="blocked", lossless=False,
            reason=(
                f"JPEG 原图 {_fmt_bytes(info['bytes'])} 超过 1MB，无损不可能再变小。"
                "请在「缩尺寸 / 换 high 档 / 换图」中选一个"
            ),
        )
        return result

    if not result["ok"]:
        return result

    # 已经够小就别动它。把一张 200KB 的图重编码一遍不会让读者看得更清楚，
    # 只会让文字边缘和线条变脏。判据是 1MB 硬上限，不是某个宽度阈值。
    if info["bytes"] <= limit and quality != "small":
        result["reason"] = f"原图 {_fmt_bytes(info['bytes'])} 已在 1MB 以内，保持原样不重编码"
        return result

    # PNG 优先走无损瘦身：图表、截图、设计稿的价值全在文字和线条上，
    # 直接转 JPEG 会把它们毁掉。
    if fmt == "PNG" and quality != "small":
        shrunk = _png_lossless_shrink(src.read_bytes())
        if shrunk and len(shrunk[0]) <= limit:
            out = out_dir / f"{_stem(src)}.png"
            out.write_bytes(shrunk[0])
            return _finish(result, out, shrunk[1], lossless=True)
        if quality == "lossless":
            result.update(
                ok=False, action="blocked", lossless=False,
                reason="PNG 无损压缩后仍超过 1MB，请改用 high 档或换图",
            )
            return result

    with Image.open(src) as im:
        im = im.convert("RGBA") if info["has_alpha"] else im.convert("RGB")
        cur_w, cur_h = im.size

        if quality == "small":
            target_w, q = min(900, cur_w), 70
        elif quality == "high":
            target_w, q = min(JPEG_MAX_W, cur_w), 92
        else:  # balanced
            target_w, q = min(JPEG_MAX_W, cur_w), 95

        if target_w < cur_w:
            cur_h = round(cur_h * target_w / cur_w)
            im = im.resize((target_w, cur_h), Image.LANCZOS)

        # 尺寸定下来之后再谈质量：顺序反了，细节在第一步就没了
        if quality == "balanced":
            lo, hi, best = 55, 95, None
            while lo <= hi:
                mid = (lo + hi) // 2
                data = _encode(im, "JPEG", mid)
                if len(data) <= limit:
                    best = (mid, data)
                    lo = mid + 1
                else:
                    hi = mid - 1
            if best is None:
                while cur_w > 600:
                    cur_w = round(cur_w * 0.9)
                    cur_h = round(cur_h * 0.9)
                    im = im.resize((cur_w, cur_h), Image.LANCZOS)
                    data = _encode(im, "JPEG", 72)
                    if len(data) <= limit:
                        best = (72, data)
                        break
            if best is None:
                result.update(ok=False, action="blocked", lossless=False,
                              reason="缩到 600px 宽仍超过 1MB，请换图")
                return result
            q, data = best
        else:
            data = _encode(im, "JPEG", q)
            tries = 0
            while len(data) > limit and q > 60 and tries < 5:
                q -= 5
                tries += 1
                data = _encode(im, "JPEG", q)
            if len(data) > limit:
                result.update(ok=False, action="blocked", lossless=False,
                              reason=f"{quality} 档压到质量 {q} 仍超过 1MB，请换图或改 small 档")
                return result

    out = out_dir / f"{_stem(src)}-{quality}.jpg"
    out.write_bytes(data)
    result.update(out=str(out), out_bytes=len(data),
                  out_bytes_text=_fmt_bytes(len(data)),
                  out_px=f"{im.size[0]}x{im.size[1]}",
                  lossless=False,
                  action="resize+reencode" if target_w < w else "reencode")
    why = "small 档强制压缩" if quality == "small" else "原图超 1MB"
    result["reason"] = (
        f"缩到 {im.size[0]}x{im.size[1]}、质量 {q}，转 JPEG（{why}）"
        if target_w < w
        else f"质量 {q} 重编码（{why}）"
    )
    return result


def _finish(result: dict, out: Path, reason: str, lossless: bool) -> dict:
    result.update(
        out=str(out),
        out_bytes=out.stat().st_size,
        out_bytes_text=_fmt_bytes(out.stat().st_size),
        action="lossless_shrink",
        lossless=lossless,
        reason=reason,
        ok=True,
    )
    return result


def _stem(p: Path) -> str:
    return hashlib.md5(str(p).encode()).hexdigest()[:10]


def verify_remote(url: str, src_px: str, src_bytes: int, timeout: int = 30) -> dict:
    """把图从 CDN 拉回来量尺寸，用证据代替承诺。

    微信以后改规则，这里会立刻暴露，而不是等读者说「图糊了」。
    """
    out = {
        "src_px": src_px,
        "cdn_px": "",
        "src_bytes": src_bytes,
        "cdn_bytes": 0,
        "lossless": False,
        "reason": "",
    }
    try:
        import requests

        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        out["cdn_bytes"] = len(r.content)
        with Image.open(io.BytesIO(r.content)) as im:
            cdn_px = f"{im.size[0]}x{im.size[1]}"
            out["cdn_px"] = cdn_px
        same_px = cdn_px == src_px
        # 尺寸一致且字节没明显缩水 → 视为服务端未做有损处理
        out["lossless"] = bool(same_px and out["cdn_bytes"] >= src_bytes * 0.9)
        if not same_px:
            out["reason"] = f"服务端改了尺寸：{src_px} → {cdn_px}"
        elif not out["lossless"]:
            out["reason"] = "尺寸未变但字节明显缩小，服务端做过重压缩"
    except Exception as e:
        out["reason"] = f"回读失败：{e}"
    return out


def qc(paths: list[str], quality: str = "balanced", limit: int = BODY_LIMIT) -> dict:
    """不上传的预演：告诉你每张图会发生什么。"""
    items = []
    for p in paths:
        try:
            items.append(prepare(p, quality, out_dir=None, limit=limit))
        except Exception as e:
            items.append({"src": p, "ok": False, "reason": f"读取失败：{e}"})
    blocked = [i for i in items if not i.get("ok")]
    return {
        "ok": not blocked,
        "quality": quality,
        "count": len(items),
        "items": items,
        "blocked": len(blocked),
        "note": "这是本地预演，不含服务端压缩；最终以 draft 后的 cdn_px 为准",
    }
