#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from credential_store import (
    default_env_file,
    prompt_for_credentials,
    prompt_should_save,
    read_credentials,
    write_credentials,
)
from id_photo_common import ensure_directory, write_json
from liblib_client import (
    DEFAULT_BASE_URL,
    IMG2IMG_TEMPLATE_UUID,
    TEXT_TEMPLATE_UUID,
    LiblibClient,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate images via Liblib text2img or img2img.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    text_parser = subparsers.add_parser("text2img", help="Run Liblib text-to-image.")
    _add_common_args(text_parser)
    text_parser.add_argument("--aspect-ratio", choices=["square", "portrait", "landscape"], default="portrait")
    text_parser.add_argument("--width", type=int, help="Custom generation width.")
    text_parser.add_argument("--height", type=int, help="Custom generation height.")
    text_parser.add_argument("--steps", type=int, default=30)
    text_parser.add_argument("--control-type", choices=["line", "depth", "pose", "IPAdapter"])
    text_parser.add_argument("--control-image", help="Public URL for control image.")
    text_parser.add_argument("--template-uuid", default=TEXT_TEMPLATE_UUID)

    image_parser = subparsers.add_parser("img2img", help="Run Liblib image-to-image.")
    _add_common_args(image_parser)
    image_parser.add_argument("--source-image-url", required=True, help="Public image URL for Liblib sourceImage.")
    image_parser.add_argument("--control-type", choices=["line", "depth", "pose", "IPAdapter"])
    image_parser.add_argument("--control-image", help="Public URL for control image.")
    image_parser.add_argument("--template-uuid", default=IMG2IMG_TEMPLATE_UUID)

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", help="Positive prompt in English.")
    parser.add_argument("--prompt-file", help="Read the prompt from a text file.")
    parser.add_argument("--img-count", type=int, default=1, choices=[1, 2, 3, 4])
    parser.add_argument("--output-dir", required=True, help="Where to save JSON metadata and downloaded images.")
    parser.add_argument("--access-key", help="Liblib AccessKey.")
    parser.add_argument("--secret-key", help="Liblib SecretKey.")
    parser.add_argument("--env-file", help="Custom env file path. Defaults to .env.local in the skill root.")
    parser.add_argument("--save-credentials", action="store_true", help="Persist provided or prompted credentials to the env file.")
    parser.add_argument("--base-url", default=os.environ.get("LIBLIB_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--wait-timeout", type=float, default=300.0)
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--no-wait", action="store_true", help="Submit the job and exit without polling.")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt.strip()
    if args.prompt_file:
        return Path(args.prompt_file).expanduser().read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
        if prompt:
            return prompt
    raise SystemExit("Provide --prompt, --prompt-file, or stdin.")


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str, Path]:
    env_file = Path(args.env_file).expanduser().resolve() if args.env_file else default_env_file()

    access_key = args.access_key or os.environ.get("LIBLIB_ACCESS_KEY")
    secret_key = args.secret_key or os.environ.get("LIBLIB_SECRET_KEY")

    if not (access_key and secret_key):
        saved_access_key, saved_secret_key = read_credentials(env_file)
        access_key = access_key or saved_access_key
        secret_key = secret_key or saved_secret_key

    prompted = False
    if not (access_key and secret_key):
        if not sys.stdin.isatty():
            raise SystemExit(
                f"Liblib credentials are missing. Ask the user for AccessKey/SecretKey or save them in {env_file}."
            )
        access_key, secret_key = prompt_for_credentials()
        prompted = True

    if args.save_credentials:
        write_credentials(access_key, secret_key, env_file)
    elif prompted and prompt_should_save(env_file):
        write_credentials(access_key, secret_key, env_file)

    return access_key, secret_key, env_file


def main() -> int:
    args = build_parser().parse_args()
    prompt = read_prompt(args)
    access_key, secret_key, env_file = resolve_credentials(args)
    output_dir = ensure_directory(args.output_dir)
    client = LiblibClient(access_key, secret_key, base_url=args.base_url)

    if args.command == "text2img":
        submission = client.text_to_image(
            prompt=prompt,
            img_count=args.img_count,
            aspect_ratio=args.aspect_ratio,
            image_width=args.width,
            image_height=args.height,
            steps=args.steps,
            control_type=args.control_type,
            control_image=args.control_image,
            template_uuid=args.template_uuid,
        )
    else:
        submission = client.image_to_image(
            prompt=prompt,
            img_count=args.img_count,
            source_image=args.source_image_url,
            control_type=args.control_type,
            control_image=args.control_image,
            template_uuid=args.template_uuid,
        )

    generate_uuid = submission.get("generateUuid")
    if not generate_uuid:
        raise SystemExit("Liblib did not return generateUuid.")

    submitted_request = {
        "command": args.command,
        "prompt": prompt,
        "generateUuid": generate_uuid,
        "outputDir": str(output_dir),
        "envFile": str(env_file),
    }
    if args.command == "text2img":
        submitted_request.update(
            {
                "aspectRatio": args.aspect_ratio,
                "width": args.width,
                "height": args.height,
                "steps": args.steps,
                "controlType": args.control_type,
                "controlImage": args.control_image,
            }
        )
    else:
        submitted_request.update(
            {
                "sourceImageUrl": args.source_image_url,
                "controlType": args.control_type,
                "controlImage": args.control_image,
            }
        )
    write_json(output_dir / "submitted-request.json", submitted_request)

    if args.no_wait:
        write_json(output_dir / "generation-result.json", submitted_request)
        print(f"submitted {generate_uuid}")
        return 0

    result = client.wait_for_completion(
        generate_uuid,
        poll_interval=args.poll_interval,
        timeout=args.wait_timeout,
    )
    downloaded = client.download_images(result.get("images") or [], output_dir)

    final_payload = {
        **submitted_request,
        "generateStatus": result.get("generateStatus"),
        "generateMsg": result.get("generateMsg"),
        "pointsCost": result.get("pointsCost"),
        "accountBalance": result.get("accountBalance"),
        "downloaded": downloaded,
        "rawResult": result,
    }
    write_json(output_dir / "generation-result.json", final_payload)
    print(output_dir / "generation-result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
