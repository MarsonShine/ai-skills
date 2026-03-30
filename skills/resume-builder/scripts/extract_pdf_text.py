#!/usr/bin/env python3
"""Extract text from one or more PDF files for resume-building workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def load_pypdf():
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(
            "Missing dependency: pypdf. Install it with `py -m pip install pypdf` "
            "or `python -m pip install pypdf` and retry."
        ) from exc
    return PdfReader


def extract_text(pdf_path: Path) -> str:
    PdfReader = load_pypdf()
    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.append(f"--- PAGE {index} ---")
        chunks.append(text.strip())
    return "\n".join(chunks).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", help="PDF file paths to extract")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output file. If omitted, prints to stdout. Valid only with one input PDF.",
    )
    args = parser.parse_args()

    pdf_paths = [Path(p).expanduser().resolve() for p in args.pdfs]
    missing = [str(p) for p in pdf_paths if not p.exists()]
    if missing:
        raise SystemExit("Missing PDF(s): " + ", ".join(missing))

    if args.output and len(pdf_paths) != 1:
        raise SystemExit("--output can only be used with one input PDF.")

    outputs: list[str] = []
    for pdf_path in pdf_paths:
        outputs.append(f"=== {pdf_path.name} ===")
        outputs.append(extract_text(pdf_path))

    combined = "\n".join(outputs).strip() + "\n"

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.write_text(combined, encoding="utf-8")
        print(f"Saved extracted text to {output_path}")
        return 0

    sys.stdout.write(combined)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
