#!/usr/bin/env python3
"""Build and verify an animated GIF from lexically ordered screenshots."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, NoReturn


DEFAULT_MAX_BYTES = 5 * 1024 * 1024


def abort(message: str) -> NoReturn:
    raise SystemExit(f"error: {message}")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        abort(f"expected an integer, got {value!r}")
    if parsed <= 0:
        abort(f"expected a positive integer, got {value!r}")
    return parsed


def positive_number(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        abort(f"expected a number, got {value!r}")
    if not math.isfinite(parsed) or parsed <= 0:
        abort(f"expected a finite positive number, got {value!r}")
    return parsed


def duration_list(raw: str, count: int) -> list[float]:
    pieces = [piece.strip() for piece in raw.split(",")]
    if not pieces or any(not piece for piece in pieces):
        abort("--durations must contain one number or a comma-separated list")
    values = [positive_number(piece) for piece in pieces]
    if len(values) == 1:
        return values * count
    if len(values) != count:
        abort(f"received {len(values)} durations for {count} frames")
    return values


def executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        abort(f"required executable {name!r} is not available on PATH")
    return resolved


def run_json(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or str(error)
        abort(detail)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        abort(f"media probe returned invalid JSON: {error}")
    if not isinstance(value, dict):
        abort("media probe returned a non-object JSON value")
    return value


def probe(ffprobe: str, path: Path, *, count_frames: bool = False) -> dict[str, Any]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
    ]
    if count_frames:
        command.append("-count_frames")
    command.extend(
        [
            "-show_entries",
            "stream=width,height,nb_frames,nb_read_frames,duration:format=duration",
            "-of",
            "json",
            str(path),
        ]
    )
    return run_json(command)


def first_stream(report: dict[str, Any], path: Path) -> dict[str, Any]:
    streams = report.get("streams")
    if not isinstance(streams, list) or not streams or not isinstance(streams[0], dict):
        abort(f"no video stream found in {path}")
    return streams[0]


def integer_field(stream: dict[str, Any], field: str, path: Path) -> int:
    try:
        value = int(stream[field])
    except (KeyError, TypeError, ValueError):
        abort(f"missing integer field {field!r} for {path}")
    if value <= 0:
        abort(f"field {field!r} must be positive for {path}")
    return value


def media_duration(report: dict[str, Any], stream: dict[str, Any], path: Path) -> float:
    candidates = [stream.get("duration")]
    format_info = report.get("format")
    if isinstance(format_info, dict):
        candidates.append(format_info.get("duration"))
    for candidate in candidates:
        try:
            value = float(candidate)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value) and value > 0:
            return value
    abort(f"missing duration for {path}")


def concat_path(path: Path) -> str:
    value = path.resolve().as_posix()
    if "\n" in value or "\r" in value:
        abort(f"frame path contains a newline: {path}")
    return "'" + value.replace("'", "'\\''") + "'"


def write_manifest(path: Path, frames: list[Path], durations: list[float]) -> None:
    rows = ["ffconcat version 1.0"]
    for frame, hold in zip(frames, durations):
        rows.extend((f"file {concat_path(frame)}", f"duration {hold:.6f}"))
    rows.append(f"file {concat_path(frames[-1])}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("frames", type=Path, help="directory containing ordered screenshots")
    result.add_argument("output", type=Path, help="destination .gif file")
    result.add_argument("--pattern", default="*.png", help="input glob inside the frame directory")
    result.add_argument("--durations", default="2", help="one hold duration or one per frame")
    result.add_argument("--fps", type=positive_int, default=10)
    result.add_argument("--max-width", type=positive_int, default=1200)
    result.add_argument("--colors", type=positive_int, default=128)
    result.add_argument("--max-bytes", type=positive_int, default=DEFAULT_MAX_BYTES)
    result.add_argument("--force", action="store_true", help="replace the exact output file")
    return result


def main() -> None:
    args = parser().parse_args()
    frame_dir = args.frames.resolve()
    output = args.output.resolve()

    if not frame_dir.is_dir():
        abort(f"frame directory does not exist: {frame_dir}")
    if output.suffix.lower() != ".gif":
        abort(f"output must use the .gif extension: {output}")
    if not 4 <= args.colors <= 256:
        abort("--colors must be between 4 and 256")
    if args.fps > 30:
        abort("--fps must not exceed 30")
    if output.exists() and not args.force:
        abort(f"output exists; pass --force to replace it: {output}")

    frames = sorted(path.resolve() for path in frame_dir.glob(args.pattern) if path.is_file())
    if len(frames) < 2:
        abort(f"expected at least two files matching {args.pattern!r} in {frame_dir}")
    if output in frames:
        abort("the output file cannot also be an input frame")

    holds = duration_list(args.durations, len(frames))
    expected_duration = sum(holds)
    ffmpeg = executable("ffmpeg")
    ffprobe = executable("ffprobe")

    dimensions: set[tuple[int, int]] = set()
    for frame in frames:
        stream = first_stream(probe(ffprobe, frame), frame)
        dimensions.add(
            (integer_field(stream, "width", frame), integer_field(stream, "height", frame))
        )
    if len(dimensions) != 1:
        abort(f"all frames must have identical dimensions, got {sorted(dimensions)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and args.force:
        output.unlink()

    with tempfile.TemporaryDirectory(prefix="browser-gif-") as temp_dir:
        manifest = Path(temp_dir) / "frames.ffconcat"
        write_manifest(manifest, frames, holds)
        filters = (
            f"fps={args.fps},scale='min({args.max_width},iw)':-2:flags=lanczos,"
            "split[gif][palette_source];"
            f"[palette_source]palettegen=max_colors={args.colors}:stats_mode=full[palette];"
            "[gif][palette]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle"
        )
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest),
            "-filter_complex",
            filters,
            "-loop",
            "0",
            "-t",
            f"{expected_duration:.6f}",
            "-n",
            str(output),
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as error:
            abort(f"ffmpeg exited with status {error.returncode}")

    report = probe(ffprobe, output, count_frames=True)
    stream = first_stream(report, output)
    width = integer_field(stream, "width", output)
    height = integer_field(stream, "height", output)
    frame_key = "nb_read_frames" if stream.get("nb_read_frames") not in (None, "N/A") else "nb_frames"
    encoded_frames = integer_field(stream, frame_key, output)
    actual_duration = media_duration(report, stream, output)
    tolerance = max(0.25, 2 / args.fps)

    if width > args.max_width:
        abort(f"encoded width {width} exceeds --max-width {args.max_width}")
    if encoded_frames < 2:
        abort(f"expected an animated GIF, encoded {encoded_frames} frame")
    if abs(actual_duration - expected_duration) > tolerance:
        abort(
            f"expected approximately {expected_duration:.3f}s, encoded {actual_duration:.3f}s"
        )

    byte_size = output.stat().st_size
    if byte_size > args.max_bytes:
        abort(f"output is {byte_size} bytes, above --max-bytes {args.max_bytes}")

    print(
        json.dumps(
            {
                "bytes": byte_size,
                "durationSeconds": actual_duration,
                "encodedFrames": encoded_frames,
                "fps": args.fps,
                "height": height,
                "output": str(output),
                "sourceFrames": len(frames),
                "width": width,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
