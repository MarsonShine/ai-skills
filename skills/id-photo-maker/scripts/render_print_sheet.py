#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from id_photo_common import (
    ensure_directory,
    file_to_data_uri,
    resolve_page_preset,
    resolve_size_spec,
    write_json,
)

ASSET_CSS = (SCRIPT_DIR.parent / "assets" / "print.css").read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render printable HTML sheets for finished ID photos.")
    parser.add_argument("--photo", required=True, help="Processed local photo path.")
    parser.add_argument("--size", required=True, help="Photo size preset or custom size.")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--pages", default="a4,6inch", help="Comma-separated page presets, e.g. a4,6inch.")
    parser.add_argument("--copies", type=int, help="Optional fixed copy count; otherwise fill the page.")
    parser.add_argument("--margin-mm", type=float, help="Override page margin.")
    parser.add_argument("--gap-mm", type=float, help="Override cell gap.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--title", default="ID Photo Print Sheet")
    return parser


def format_mm(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def build_page_layout(size_spec: dict, page_spec: dict, requested_copies: int | None) -> dict:
    margin_mm = float(page_spec["margin_mm"])
    gap_mm = float(page_spec["gap_mm"])
    meta_height_mm = 13.0
    usable_width_mm = float(page_spec["width_mm"]) - margin_mm * 2
    usable_height_mm = float(page_spec["height_mm"]) - margin_mm * 2 - meta_height_mm

    photo_width_mm = float(size_spec["width_mm"])
    photo_height_mm = float(size_spec["height_mm"])
    columns = max(1, math.floor((usable_width_mm + gap_mm) / (photo_width_mm + gap_mm)))
    rows = max(1, math.floor((usable_height_mm + gap_mm) / (photo_height_mm + gap_mm)))
    max_copies = columns * rows
    copies = min(requested_copies, max_copies) if requested_copies else max_copies

    return {
        "columns": columns,
        "rows": rows,
        "copies": copies,
        "maxCopies": max_copies,
        "metaHeightMm": meta_height_mm,
    }


def render_page_html(
    *,
    page_spec: dict,
    size_spec: dict,
    title: str,
    photo_data_uri: str,
    layout: dict,
) -> str:
    page_css = page_spec["page_css"]
    margin_mm = page_spec["margin_mm"]
    gap_mm = page_spec["gap_mm"]
    photo_width_mm = size_spec["width_mm"]
    photo_height_mm = size_spec["height_mm"]
    columns = layout["columns"]
    copies = layout["copies"]

    cells = "\n".join(
        f'        <figure class="photo-cell"><img src="{photo_data_uri}" alt="ID photo copy {index + 1}"></figure>'
        for index in range(copies)
    )

    safe_title = html.escape(title)
    page_label = html.escape(str(page_spec["label"]))
    size_label = html.escape(str(size_spec["label"]))

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} - {page_label}</title>
  <style>{ASSET_CSS}</style>
  <style>
    @page {{
      size: {page_css};
      margin: 0;
    }}

    .sheet {{
      width: {format_mm(float(page_spec["width_mm"]))}mm;
      height: {format_mm(float(page_spec["height_mm"]))}mm;
      padding: {format_mm(float(margin_mm))}mm;
    }}

    .photo-grid {{
      grid-template-columns: repeat({columns}, {format_mm(float(photo_width_mm))}mm);
      gap: {format_mm(float(gap_mm))}mm;
    }}

    .photo-cell,
    .photo-cell img {{
      width: {format_mm(float(photo_width_mm))}mm;
      height: {format_mm(float(photo_height_mm))}mm;
    }}
  </style>
</head>
<body>
  <main class="print-shell">
    <section class="sheet">
      <header class="sheet__meta">
        <div>
          <h1 class="sheet__title">{safe_title}</h1>
          <p class="sheet__hint">Print at 100% scale. Do not enable browser shrink-to-fit.</p>
        </div>
        <div>
          <div>Page: {page_label}</div>
          <div>Photo size: {size_label}</div>
          <div>Copies: {copies}</div>
        </div>
      </header>
      <div class="photo-grid">
{cells}
      </div>
    </section>
  </main>
</body>
</html>
"""


def build_index(title: str, outputs: list[dict]) -> str:
    items = "\n".join(
        (
            "        <li>"
            f'<a href="{html.escape(output["fileName"])}">{html.escape(output["label"])}</a>'
            f' — {output["copies"]} copies'
            "</li>"
        )
        for output in outputs
    )
    safe_title = html.escape(title)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>{ASSET_CSS}</style>
</head>
<body>
  <main class="index">
    <section class="index__card">
      <h1>{safe_title}</h1>
      <p class="index__meta">Open the target page below in a browser and print at 100% scale.</p>
      <ol class="index__list">
{items}
      </ol>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    args = build_parser().parse_args()
    output_dir = ensure_directory(args.output_dir)
    photo_path = Path(args.photo).expanduser().resolve()
    if not photo_path.is_file():
        raise SystemExit(f"Photo not found: {photo_path}")

    size_spec = resolve_size_spec(args.size, dpi=args.dpi)
    photo_data_uri = file_to_data_uri(photo_path)
    page_keys = [entry.strip() for entry in args.pages.split(",") if entry.strip()]
    outputs: list[dict] = []

    for page_key in page_keys:
        page_spec = resolve_page_preset(page_key)
        if args.margin_mm is not None:
            page_spec["margin_mm"] = args.margin_mm
        if args.gap_mm is not None:
            page_spec["gap_mm"] = args.gap_mm

        layout = build_page_layout(size_spec, page_spec, args.copies)
        html_payload = render_page_html(
            page_spec=page_spec,
            size_spec=size_spec,
            title=args.title,
            photo_data_uri=photo_data_uri,
            layout=layout,
        )
        target_name = f"print-{page_spec['key']}.html"
        target_path = output_dir / target_name
        target_path.write_text(html_payload, encoding="utf-8")
        outputs.append(
            {
                "key": page_spec["key"],
                "label": page_spec["label"],
                "fileName": target_name,
                "path": str(target_path),
                "copies": layout["copies"],
                "columns": layout["columns"],
                "rows": layout["rows"],
            }
        )

    index_html = build_index(args.title, outputs)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")
    write_json(
        output_dir / "print-sheet.json",
        {
            "title": args.title,
            "photo": str(photo_path),
            "size": size_spec,
            "outputs": outputs,
        },
    )
    print(output_dir / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
