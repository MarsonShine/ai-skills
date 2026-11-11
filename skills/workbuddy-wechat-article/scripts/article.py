"""One CLI for the WorkBuddy WeChat article workflow.

Commands mirror the writing loop: profile -> check -> rewrite -> preview -> draft.
Every command prints one JSON object so an agent can act on the result.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import uuid
from typing import Any

import blocks
import images
import profile as profile_module
import publish
import render
import rewrite
import voice


def emit(data: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(data, ensure_ascii=False))
    return code


def fail(error: Any, code: int = 2, **extra: Any) -> int:
    message = str(error) if not isinstance(error, str) else error
    payload = {"ok": False, "code": code, "error": message, **extra}
    return emit(payload, code)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _excerpt(text: str, length: int) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    return flat[:length].rstrip()


def _title_and_digest(document: dict[str, Any]) -> tuple[str, str]:
    text = blocks.text_content(document["blocks"])
    title = (document.get("title") or "").strip()
    if not title:
        first = blocks.split_sentences(blocks.clean_with_map(text)[0])
        title = _excerpt(first[0][2] if first else text, 32)
    digest = (document.get("digest") or "").strip() or _excerpt(text, 54)
    if not title:
        raise ValueError("正文为空，无法生成标题。")
    if len(title) > 64:
        raise ValueError("标题超过微信 64 字限制。")
    if len(digest) > 120:
        raise ValueError("摘要超过微信 120 字限制。")
    return title, digest


def _profile(args: argparse.Namespace, workdir: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    return profile_module.resolve(args.profile if hasattr(args, "profile") else None, workdir)


def _load_document(args: argparse.Namespace) -> dict[str, Any]:
    if not getattr(args, "text", None) and not getattr(args, "blocks", None):
        raise ValueError("请提供 --blocks 或 --text 中的一项。")
    if getattr(args, "text", None):
        text = Path(args.text).expanduser().resolve().read_text(encoding="utf-8-sig")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        document = {"blocks": [{"type": "p", "text": part} for part in paragraphs]}
    else:
        document = blocks.load_document(args.blocks)
    profile, source = _profile(args, Path(args.workdir).resolve() if getattr(args, "workdir", None) else None)
    if profile:
        document["scene"] = document.get("scene") or profile["typesetting"]["scene"]
        document.setdefault("author", profile["identity"]["name"])
        document["profile"] = profile
    if getattr(args, "scene", None):
        document["scene"] = args.scene
    document["scene"] = document.get("scene") or "daily"
    return document


def _prepare(
    document: dict[str, Any],
    workdir: Path,
    quality: str,
    max_width: int,
    cover_path: str | None,
) -> tuple[Path, list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    image_dir = workdir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    body_sources = _body_sources(document)
    mapping: dict[str, str] = {}
    measurements: list[dict[str, Any]] = []
    for index, source in enumerate(body_sources, start=1):
        stem = f"body-{index:02d}"
        measurement = images.prepare(source, image_dir, stem, quality, "body", max_width=max_width)
        relative = "images/" + Path(measurement["path"]).name
        mapping[source] = relative
        measurements.append({**measurement, "src": source})
    cover_source = cover_path or document.get("cover") or (body_sources[0] if body_sources else None)
    if not cover_source:
        return image_dir, measurements, {}, mapping
    cover_measurement = images.prepare(cover_source, image_dir, "cover", quality, "cover", max_width=max_width)
    cover_relative = "images/" + Path(cover_measurement["path"]).name
    cover = {
        "src": cover_source,
        "path": cover_relative,
        "sha256": cover_measurement["sha256"],
        "measurement": {
            key: value for key, value in cover_measurement.items() if key not in {"src", "path"}
        },
    }
    return image_dir, measurements, cover, mapping


def _body_sources(document: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    for block in document["blocks"]:
        kind = block.get("type")
        keys = ("src",) if kind in {"image", "photo_polaroid"} else ("a", "b") if kind == "compare_pair" else ()
        for key in keys:
            value = block.get(key)
            if isinstance(value, str) and value and value not in sources:
                sources.append(value)
    return sources


def _bundle(
    document: dict[str, Any],
    workdir: Path,
    scene: str,
    quality: str,
    title: str,
    digest: str,
    author: str,
    article: str,
    measurements: list[dict[str, Any]],
    cover: dict[str, Any],
) -> dict[str, Any]:
    identity_file = workdir / ".article-id"
    if identity_file.is_file():
        article_id = identity_file.read_text(encoding="utf-8").strip()
    else:
        article_id = str(uuid.uuid4())
        identity_file.write_text(article_id, encoding="utf-8")
    bundle = {
        "schema": 1,
        "articleId": article_id,
        "title": title,
        "digest": digest,
        "author": author,
        "scene": scene,
        "quality": quality,
        "typesetting": (document.get("profile") or {}).get("typesetting", {}),
        "blocks": document["blocks"],
        "html": article,
        "images": [
            {
                "src": item["src"],
                "path": "images/" + Path(item["path"]).name,
                "sha256": item["sha256"],
                "measurement": {key: value for key, value in item.items() if key not in {"src", "path"}},
            }
            for item in measurements
        ],
        "cover": cover,
        "createdAt": _utc_now(),
    }
    bundle["version"] = publish.bundle_version(bundle)
    (workdir / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return bundle


def _guard(document: dict[str, Any], selected: dict[str, Any] | None) -> list[str]:
    """Enforce the profile's privacy and topic boundaries before rendering."""
    if not selected:
        return []
    text = blocks.text_content(document["blocks"])
    warnings: list[str] = []
    if not selected["family"]["ok_to_write"]:
        for member in selected["family"]["members"]:
            nickname = member.get("nickname", "")
            if nickname and nickname in text:
                raise ValueError(f"作者设置不写家人，但正文出现“{nickname}”。")
    for item in selected["taboo"]["private"]:
        if item and item in text:
            raise ValueError(f"正文包含作者标记为隐私的内容：“{item}”。")
    for topic in selected["taboo"]["topics"]:
        if topic and topic in text:
            warnings.append(f"正文触及作者声明不写的题材：“{topic}”。")
    return warnings


def command_profile(args: argparse.Namespace) -> int:
    if args.example:
        sys.stdout.write(profile_module.example())
        return 0
    if args.questions:
        return emit({"ok": True, "questions": profile_module.questions()})
    if args.answers:
        answers = json.loads(Path(args.answers).expanduser().resolve().read_text(encoding="utf-8-sig"))
        selected = profile_module.from_answers(answers)
        saved = profile_module.save(selected, args.save) if args.save else None
        return emit(
            {
                "ok": True,
                "profile": selected,
                "source": "answers",
                "saved": str(saved) if saved else None,
                "contract": profile_module.style_contract(selected),
            }
        )
    if args.file:
        selected = profile_module.load(args.file)
        return emit(
            {
                "ok": True,
                "profile": selected,
                "source": str(Path(args.file).resolve()),
                "contract": profile_module.style_contract(selected),
            }
        )
    selected, source = profile_module.resolve(args.profile, args.workdir)
    if selected is None:
        return emit(
            {
                "ok": True,
                "profile": None,
                "source": None,
                "message": "还没有作者档案。用 12 题问卷初始化，或手写 profile.yaml。",
                "questions": profile_module.questions(),
            }
        )
    return emit(
        {
            "ok": True,
            "profile": selected,
            "source": source,
            "contract": profile_module.style_contract(selected),
        }
    )


def command_check(args: argparse.Namespace) -> int:
    document = _load_document(args)
    selected = document.get("profile")
    warnings = _guard(document, selected)
    report = voice.analyze(document, selected, args.scene or document.get("scene"))
    if warnings:
        report["warnings"] = warnings
    if args.out:
        Path(args.out).expanduser().resolve().write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        report["reportPath"] = str(Path(args.out).expanduser().resolve())
    code = 4 if args.fail_under is not None and report["scores"]["final"] < args.fail_under else 0
    return emit({"ok": code == 0, "report": report}, code)


def command_rewrite(args: argparse.Namespace) -> int:
    document = blocks.load_document(args.blocks)
    report = rewrite.load_json(args.report)
    if isinstance(report, dict) and isinstance(report.get("report"), dict):
        report = report["report"]
    rewrites = rewrite.load_json(args.rewrites)
    result = rewrite.apply(document, report, rewrites)
    out = Path(args.out).expanduser().resolve()
    out.write_text(json.dumps(result["document"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.changes:
        Path(args.changes).expanduser().resolve().write_text(
            json.dumps(
                {"changes": result["changes"], "rejected": result["rejected"], "keep": result["keep"]},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return emit(
        {
            "ok": True,
            "documentPath": str(out),
            "structure_ok": result["structure_ok"],
            "applied": result["applied"],
            "rejected": result["rejected"],
            "keep": result["keep"],
            "changes": result["changes"],
        }
    )


def command_render(args: argparse.Namespace) -> int:
    document = _load_document(args)
    selected = document.get("profile")
    image_map = rewrite.load_json(args.image_map) if args.image_map else None
    if image_map is not None and not isinstance(image_map, dict):
        raise ValueError("--image-map 应为 {原图路径: URL} 的 JSON 对象")
    report = rewrite.load_json(args.voice) if args.voice else None
    if isinstance(report, dict) and isinstance(report.get("report"), dict):
        report = report["report"]
    if report is not None and not isinstance(report, dict):
        raise ValueError("--voice 应为 check 输出的报告对象")
    info = render.write_outputs(
        document,
        args.out_dir,
        image_map=image_map,
        scene=args.scene or document.get("scene"),
        profile=selected,
        voice_report=report,
    )
    return emit(info)


def command_preview(args: argparse.Namespace) -> int:
    document = _load_document(args)
    selected = document.get("profile")
    scene = args.scene or document.get("scene") or "daily"
    if scene == "auto":
        scene = "daily"
    workdir = Path(args.workdir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    guard_warnings = _guard(document, selected)
    title, digest = _title_and_digest(document)
    author = (document.get("author") or (selected or {}).get("identity", {}).get("name", "")).strip()
    if len(author) > 16:
        raise ValueError("作者署名超过 16 字。")
    image_dir, measurements, cover, mapping = _prepare(document, workdir, args.quality, args.max_width, args.cover)
    document = {**document, "title": title, "digest": digest, "author": author, "scene": scene}
    report = None if args.no_check else voice.analyze(document, selected, scene)
    if report is not None:
        (workdir / "voice.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    info = render.write_outputs(
        document,
        workdir,
        image_map=mapping,
        scene=scene,
        profile=selected,
        images=measurements
        + (
            [{**cover["measurement"], "src": cover["src"], "role": "cover"}]
            if cover
            else []
        ),
        voice_report=report,
        extra_warnings=guard_warnings,
    )
    article = (workdir / "article.html").read_text(encoding="utf-8")
    bundle = _bundle(document, workdir, scene, args.quality, title, digest, author, article, measurements, cover)
    result = {
        **info,
        "workdir": str(workdir),
        "bundlePath": str(workdir / "bundle.json"),
        "version": bundle["version"],
        "quality": args.quality,
        "cover": cover.get("measurement"),
        "voice": None
        if report is None
        else {
            "final": report["scores"]["final"],
            "band": report["scores"]["band"],
            "issues": len(report["issues"]),
            "keep": len(report["keep"]),
            "targets": len(report["targets"]),
        },
    }
    if args.account:
        result["account"] = args.account
        result["action"] = args.action
        result["confirmation"] = publish.confirm_code(args.account, args.action, bundle["version"])
    return emit(result)


def command_qc(args: argparse.Namespace) -> int:
    document = _load_document(args)
    workdir = Path(args.workdir).expanduser().resolve() if args.workdir else Path(args.out_dir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    body_sources = _body_sources(document)
    results = []
    for index, source in enumerate(body_sources, start=1):
        measurement = images.prepare(source, workdir, f"body-{index:02d}", args.quality, "body", max_width=args.max_width)
        results.append({**measurement, "src": source})
    if body_sources:
        cover_source = args.cover or document.get("cover") or body_sources[0]
        cover = images.prepare(cover_source, workdir, "cover", args.quality, "cover", max_width=args.max_width)
        results.append({**cover, "src": cover_source})
    return emit({"ok": True, "quality": args.quality, "images": results})


def command_confirm(args: argparse.Namespace) -> int:
    bundle, _ = publish.load_bundle(args.workdir)
    code = publish.confirm_code(args.account, args.action, bundle["version"])
    return emit(
        {
            "ok": True,
            "account": args.account,
            "action": args.action,
            "title": bundle["title"],
            "version": bundle["version"],
            "confirmation": code,
        }
    )


def command_draft(args: argparse.Namespace) -> int:
    result = publish.draft(
        args.workdir,
        args.account,
        args.action,
        args.confirmed,
        media_id=args.media_id,
        appid=args.appid,
        secret=args.secret,
        verify=not args.no_verify,
    )
    return emit(result)


class Parser(argparse.ArgumentParser):
    """Argparse that keeps the JSON output contract on usage errors."""

    def error(self, message: str) -> None:
        print(json.dumps({"ok": False, "code": 2, "error": message}, ensure_ascii=False))
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)

    profile = sub.add_parser("profile", help="初始化或读取作者档案")
    profile.add_argument("--file")
    profile.add_argument("--answers")
    profile.add_argument("--save")
    profile.add_argument("--workdir")
    profile.add_argument("--profile")
    profile.add_argument("--example", action="store_true")
    profile.add_argument("--questions", action="store_true")
    profile.set_defaults(func=command_profile)

    for name, func, help_text in (
        ("check", command_check, "检测 AI 味并输出报告"),
        ("render", command_render, "只渲染 HTML 与预览"),
        ("preview", command_preview, "处理图片、检测并生成预览包"),
        ("qc", command_qc, "不上传，只预演图片预处理结果"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--blocks")
        command.add_argument("--text")
        command.add_argument("--workdir")
        command.add_argument("--profile")
        command.add_argument("--scene")
        command.set_defaults(func=func)
    check = sub.choices["check"]
    check.add_argument("--out")
    check.add_argument("--fail-under", type=int, default=None)

    rewrite_command = sub.add_parser("rewrite", help="应用经过校验的定点改写")
    rewrite_command.add_argument("--blocks", required=True)
    rewrite_command.add_argument("--report", required=True)
    rewrite_command.add_argument("--rewrites", required=True)
    rewrite_command.add_argument("--out", required=True)
    rewrite_command.add_argument("--changes")
    rewrite_command.set_defaults(func=command_rewrite)

    render_command = sub.choices["render"]
    render_command.add_argument("--out-dir", required=True)
    render_command.add_argument("--image-map")
    render_command.add_argument("--voice")

    preview = sub.choices["preview"]
    preview.add_argument("--quality", choices=images.QUALITIES, default="balanced")
    preview.add_argument("--max-width", type=int, default=1280)
    preview.add_argument("--cover")
    preview.add_argument("--no-check", action="store_true")
    preview.add_argument("--account")
    preview.add_argument("--action", choices=("draft", "update"), default="draft")

    qc = sub.choices["qc"]
    qc.add_argument("--quality", choices=images.QUALITIES, default="balanced")
    qc.add_argument("--max-width", type=int, default=1280)
    qc.add_argument("--out-dir", default=".workbuddy-qc")
    qc.add_argument("--cover")

    confirm = sub.add_parser("confirm", help="为当前预览生成确认码")
    confirm.add_argument("--workdir", required=True)
    confirm.add_argument("--account", required=True)
    confirm.add_argument("--action", choices=("draft", "update"), default="draft")
    confirm.set_defaults(func=command_confirm)

    draft = sub.add_parser("draft", help="上传图片并新建或更新草稿")
    draft.add_argument("--workdir", required=True)
    draft.add_argument("--account", required=True)
    draft.add_argument("--action", choices=("draft", "update"), default="draft")
    draft.add_argument("--confirmed", required=True)
    draft.add_argument("--media-id")
    draft.add_argument("--appid")
    draft.add_argument("--secret")
    draft.add_argument("--no-verify", action="store_true")
    draft.set_defaults(func=command_draft)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except images.LosslessError as error:
        return fail(error, 7, options=getattr(error, "options", []))
    except publish.WechatError as error:
        return fail(error, 8, errcode=error.code, ambiguous=error.ambiguous)
    except (
        blocks.DocumentError,
        profile_module.ProfileError,
        render.RenderError,
        rewrite.RewriteError,
        publish.ConfigError,
        images.ImageError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
    ) as error:
        return fail(error, 2)


if __name__ == "__main__":
    raise SystemExit(main())
