#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
from pathlib import Path


def ensure_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required for the cross-platform contact-sheet backend. "
            "Install it with 'python -m pip install pillow'."
        ) from exc

    return Image, ImageDraw, ImageFont, ImageOps


def load_font(image_font, font_size: int):
    font_candidates = []

    env_value = os.environ.get("PHOTO_SELECTOR_FONT")

    if env_value:
        font_candidates.append(env_value)

    font_candidates.extend(
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/Library/Fonts/Menlo.ttc",
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/CascadiaMono.ttf",
            "DejaVuSansMono.ttf",
            "LiberationMono-Regular.ttf",
            "Menlo.ttc",
            "consola.ttf",
        ]
    )

    for candidate in font_candidates:
        try:
            return image_font.truetype(candidate, size=font_size)
        except OSError:
            continue

    return image_font.load_default()


def parse_args(argv: list[str]):
    if len(argv) == 2 and argv[1] == "--check-deps":
        ensure_pillow()
        return None

    if len(argv) < 7:
        raise SystemExit(
            "usage: contact_sheet_pillow.py output cols rows cellWidth cellHeight img1 [img2 ...]"
        )

    output = Path(argv[1])

    try:
        cols = int(argv[2])
        rows = int(argv[3])
        cell_width = int(argv[4])
        cell_height = int(argv[5])
    except ValueError as exc:
        raise SystemExit("cols, rows, cellWidth, and cellHeight must be integers.") from exc

    files = [Path(arg) for arg in argv[6:]]
    if not files:
        raise SystemExit("At least one image path is required.")

    return output, cols, rows, cell_width, cell_height, files


def render_sheet(
    output: Path,
    cols: int,
    rows: int,
    cell_width: int,
    cell_height: int,
    files: list[Path],
) -> None:
    image, image_draw, image_font, image_ops = ensure_pillow()

    sheet_width = cols * cell_width
    sheet_height = rows * cell_height
    label_height = 26
    pad = 12
    label_color = (38, 38, 38)

    sheet = image.new("RGB", (sheet_width, sheet_height), (255, 255, 255))
    draw = image_draw.Draw(sheet)
    font = load_font(image_font, 16)

    resampling = getattr(getattr(image, "Resampling", image), "LANCZOS", image.LANCZOS)

    for index, file_path in enumerate(files):
        if not file_path.is_file():
            raise SystemExit(f"Image not found: {file_path}")

        col = index % cols
        row = index // cols
        cell_x = col * cell_width
        cell_y = row * cell_height

        try:
            with image.open(file_path) as raw_image:
                working_image = image_ops.exif_transpose(raw_image)
                if working_image.mode != "RGB":
                    working_image = working_image.convert("RGB")

                available_width = max(1, cell_width - pad * 2)
                available_height = max(1, cell_height - label_height - pad * 2)
                working_image.thumbnail((available_width, available_height), resampling)

                dst_x = cell_x + pad + (available_width - working_image.width) // 2
                dst_y = cell_y + label_height + pad + (available_height - working_image.height) // 2
                sheet.paste(working_image, (dst_x, dst_y))
        except SystemExit:
            raise
        except Exception as exc:
            raise SystemExit(f"Failed to render image '{file_path}': {exc}") from exc

        draw.text((cell_x + 10, cell_y + 4), file_path.name, fill=label_color, font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="JPEG", quality=82)


def main(argv: list[str]) -> int:
    parsed = parse_args(argv)
    if parsed is None:
        print("ok")
        return 0

    output, cols, rows, cell_width, cell_height, files = parsed
    render_sheet(output, cols, rows, cell_width, cell_height, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
