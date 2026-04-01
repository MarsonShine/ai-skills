#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from getpass import getpass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_ENV_FILE = SKILL_ROOT / ".env.local"


def default_env_file() -> Path:
    return DEFAULT_ENV_FILE


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_credentials(env_file: str | Path | None = None) -> tuple[str | None, str | None]:
    path = Path(env_file).expanduser().resolve() if env_file else default_env_file()
    values = _parse_env_file(path)
    access_key = values.get("LIBLIB_ACCESS_KEY") or os.environ.get("LIBLIB_ACCESS_KEY")
    secret_key = values.get("LIBLIB_SECRET_KEY") or os.environ.get("LIBLIB_SECRET_KEY")
    return access_key, secret_key


def write_credentials(
    access_key: str,
    secret_key: str,
    env_file: str | Path | None = None,
) -> Path:
    path = Path(env_file).expanduser().resolve() if env_file else default_env_file()
    values = _parse_env_file(path)
    values["LIBLIB_ACCESS_KEY"] = access_key.strip()
    values["LIBLIB_SECRET_KEY"] = secret_key.strip()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "# Local Liblib credentials for id-photo-maker\n"
            f"LIBLIB_ACCESS_KEY={values['LIBLIB_ACCESS_KEY']}\n"
            f"LIBLIB_SECRET_KEY={values['LIBLIB_SECRET_KEY']}\n"
        ),
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def clear_credentials(env_file: str | Path | None = None) -> Path:
    path = Path(env_file).expanduser().resolve() if env_file else default_env_file()
    if path.exists():
        path.unlink()
    return path


def prompt_for_credentials() -> tuple[str, str]:
    access_key = input("Liblib AccessKey: ").strip()
    secret_key = getpass("Liblib SecretKey: ").strip()
    if not access_key or not secret_key:
        raise SystemExit("Both AccessKey and SecretKey are required.")
    return access_key, secret_key


def prompt_should_save(env_file: str | Path | None = None) -> bool:
    path = Path(env_file).expanduser().resolve() if env_file else default_env_file()
    answer = input(f"Save credentials to {path}? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage stored Liblib credentials.")
    parser.add_argument("--env-file", help="Custom .env path.")
    parser.add_argument("--show-path", action="store_true", help="Print the credential file path.")
    parser.add_argument("--read", action="store_true", help="Print whether credentials are available.")
    parser.add_argument("--save", action="store_true", help="Prompt for and save credentials.")
    parser.add_argument("--clear", action="store_true", help="Delete the stored credential file.")
    parser.add_argument("--access-key", help="AccessKey to save.")
    parser.add_argument("--secret-key", help="SecretKey to save.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    env_file = Path(args.env_file).expanduser().resolve() if args.env_file else default_env_file()

    if args.show_path:
        print(env_file)
        return 0

    if args.clear:
        clear_credentials(env_file)
        print(f"Removed {env_file}")
        return 0

    if args.save:
        access_key = args.access_key
        secret_key = args.secret_key
        if not (access_key and secret_key):
            access_key, secret_key = prompt_for_credentials()
        path = write_credentials(access_key, secret_key, env_file)
        print(f"Saved credentials to {path}")
        return 0

    if args.read:
        access_key, secret_key = read_credentials(env_file)
        status = "configured" if access_key and secret_key else "missing"
        print(f"{status} {env_file}")
        return 0

    raise SystemExit("Choose one of --show-path, --read, --save, or --clear.")


if __name__ == "__main__":
    raise SystemExit(main())
