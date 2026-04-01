#!/usr/bin/env python3

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from id_photo_common import (
    download_file,
    ensure_directory,
    is_url,
    parse_color,
    resolve_framing,
    resolve_size_spec,
    write_json,
)


def ensure_pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required for photo processing. Install it with "
            "'python3 -m pip install -r ~/.copilot/skills/id-photo-maker/requirements.txt'."
        ) from exc

    return Image, ImageOps


def ensure_rembg():
    try:
        from rembg import remove
    except ImportError as exc:
        raise SystemExit(
            "rembg is required for automatic background removal. Install it with "
            "'python3 -m pip install -r ~/.copilot/skills/id-photo-maker/requirements.txt'."
        ) from exc

    return remove


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process a local or public photo into an ID-photo asset.")
    parser.add_argument("input_source", help="Local file path or public image URL.")
    parser.add_argument("--size", required=True, help="Preset or custom size, such as 1寸, 2寸, 35x45mm, 413x579px.")
    parser.add_argument("--background", required=True, help="white, blue, red, #RRGGBB, or R,G,B.")
    parser.add_argument("--framing", default="standard", help="standard, half-body, or full-body.")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-name", default="id-photo")
    parser.add_argument("--skip-background-removal", action="store_true")
    parser.add_argument("--keep-intermediate", action="store_true")
    parser.add_argument("--subject-height-ratio", type=float, help="Override the framing preset subject height ratio.")
    parser.add_argument("--top-margin-ratio", type=float, help="Override the framing preset top margin ratio.")
    return parser


def load_source(input_source: str, output_dir: Path) -> tuple[Path, bool]:
    if is_url(input_source):
        downloaded_path = download_file(input_source, output_dir / "source")
        return downloaded_path, True

    path = Path(input_source).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"Input image not found: {path}")
    return path, False


def load_image(path: Path):
    image, image_ops = ensure_pillow()
    with image.open(path) as raw:
        working = image_ops.exif_transpose(raw).convert("RGBA")
    return image, working


def remove_background(image_module, rgba_image):
    remove = ensure_rembg()
    with io.BytesIO() as input_buffer:
        rgba_image.save(input_buffer, format="PNG")
        result_bytes = remove(input_buffer.getvalue())
    with io.BytesIO(result_bytes) as output_buffer:
        result = image_module.open(output_buffer).convert("RGBA")
    return result


def subject_bbox(rgba_image):
    alpha_channel = rgba_image.getchannel("A")
    mask = alpha_channel.point(lambda value: 255 if value >= 12 else 0)
    return mask.getbbox()


def fit_subject(
    image_module,
    subject_image,
    size_spec: dict,
    framing_spec: dict,
    background_rgb: tuple[int, int, int],
):
    target_width = int(size_spec["width_px"])
    target_height = int(size_spec["height_px"])
    canvas = image_module.new("RGBA", (target_width, target_height), (*background_rgb, 255))

    bbox = subject_bbox(subject_image)
    cropped = subject_image.crop(bbox) if bbox else subject_image
    if cropped.width <= 0 or cropped.height <= 0:
        raise SystemExit("Could not detect a subject region in the processed image.")

    desired_height = max(1, round(target_height * float(framing_spec["subject_height_ratio"])))
    scale = desired_height / cropped.height
    width_limit_scale = (target_width * 0.94) / cropped.width
    scale = min(scale, width_limit_scale)
    if scale <= 0:
        scale = min(target_width / cropped.width, target_height / cropped.height)

    resampling = getattr(getattr(image_module, "Resampling", image_module), "LANCZOS", image_module.LANCZOS)
    resized = cropped.resize(
        (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))),
        resampling,
    )

    left = max(0, (target_width - resized.width) // 2)
    top = max(0, round(target_height * float(framing_spec["top_margin_ratio"])))
    if top + resized.height > target_height:
        top = max(0, target_height - resized.height)

    canvas.alpha_composite(resized, (left, top))
    return canvas, cropped


def main() -> int:
    args = build_parser().parse_args()
    output_dir = ensure_directory(args.output_dir)
    source_path, downloaded = load_source(args.input_source, output_dir)

    image_module, rgba_image = load_image(source_path)
    processed_rgba = rgba_image if args.skip_background_removal else remove_background(image_module, rgba_image)

    size_spec = resolve_size_spec(args.size, dpi=args.dpi)
    framing_spec = resolve_framing(args.framing)
    if args.subject_height_ratio is not None:
        framing_spec["subject_height_ratio"] = args.subject_height_ratio
    if args.top_margin_ratio is not None:
        framing_spec["top_margin_ratio"] = args.top_margin_ratio

    background_rgb, background_hex = parse_color(args.background)
    final_image, cropped_subject = fit_subject(
        image_module,
        processed_rgba,
        size_spec,
        framing_spec,
        background_rgb,
    )

    final_path = output_dir / f"{args.output_name}.png"
    final_image.save(final_path, format="PNG", compress_level=1)

    metadata = {
        "inputSource": args.input_source,
        "resolvedSourcePath": str(source_path),
        "downloadedFromUrl": downloaded,
        "size": size_spec,
        "background": {
            "input": args.background,
            "hex": background_hex,
            "rgb": list(background_rgb),
        },
        "framing": framing_spec,
        "skipBackgroundRemoval": args.skip_background_removal,
        "outputPath": str(final_path),
        "dpi": args.dpi,
    }

    if args.keep_intermediate:
        cutout_path = output_dir / f"{args.output_name}-cutout.png"
        cropped_subject.save(cutout_path, format="PNG", compress_level=1)
        metadata["cutoutPath"] = str(cutout_path)

    write_json(output_dir / "metadata.json", metadata)
    print(final_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
