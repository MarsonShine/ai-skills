#!/usr/bin/env python3
"""workbuddy-wechat-mp-publisher 的唯一命令行入口。

约定：
- **stdout 只有一个 JSON**，日志一律走 stderr。agent 直接解析 stdout，不用猜。
- 退出码区分失败类型，见 EXIT 常量。agent 据此决定「改参数 / 加白 IP / 换图」。
- 凭据永不进 stdout。

用法：
  python3 scripts/wx_publish.py check
  python3 scripts/wx_publish.py preview --images a.jpg b.jpg --text-file copy.txt --scene family
  python3 scripts/wx_publish.py draft   --images ./photos --text-file copy.txt --quality lossless
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import images as images_mod          # noqa: E402
import llm                           # noqa: E402
import pipeline                      # noqa: E402
import profile as profile_mod        # noqa: E402
import state                         # noqa: E402
import voice                         # noqa: E402
import wx                            # noqa: E402

EXIT = {
    "ok": 0,
    "args": 2,
    "cred": 3,
    "ip": 4,
    "wx": 5,
    "readback": 6,
    "image": 7,
    "profile": 8,
}


def log(msg: str) -> None:
    print(f"[wagent] {msg}", file=sys.stderr, flush=True)


def out(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


# ------------------------------------------------------------------ 参数
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wx_publish",
        description="微信公众号图文排版与草稿箱发布（永不自动发表）",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp, draft=False):
        sp.add_argument("--images", nargs="+", help="图片路径，可传多个或直接传目录")
        sp.add_argument("--text", help="一段文案")
        sp.add_argument("--text-file", help="从文件读文案（UTF-8）")
        sp.add_argument("--post", help="post.json 批量模式")
        sp.add_argument("--scene", "--theme", dest="scene",
                        help="主题：magazine/minimal/tech/family/travel/daily/anniversary")
        sp.add_argument("--quality", default="balanced",
                        choices=list(images_mod.QUALITIES), help="图片质量档案")
        sp.add_argument("--rewrite", action="store_true", help="允许模型改写标题/导语/过渡")
        sp.add_argument("--profile", help="profile.yaml 路径")
        sp.add_argument("--workdir", default="./.wechat-mp", help="产物目录")
        sp.add_argument("--max-rounds", type=int, default=2, help="定点重写最大轮数")
        sp.add_argument("--no-voice", action="store_true", help="跳过去 AI 味诊断")
        if draft:
            sp.add_argument("--cover", help="封面图，默认用第一张")
            sp.add_argument("--force-new", action="store_true", help="即使同指纹也新建草稿")

    sp = sub.add_parser("init", help="生成人格文件（模板或问卷）")
    sp.add_argument("--out", default="~/.wagent/profile.yaml")
    sp.add_argument("--template", action="store_true", help="输出带注释的手填模板")
    sp.add_argument("--answers", help="问卷答案 JSON")

    sub.add_parser("check", help="验证凭据、网络与 IP 白名单")

    sp = sub.add_parser("qc", help="图片质量预演（不上传）")
    sp.add_argument("--images", nargs="+", required=True)
    sp.add_argument("--quality", default="balanced", choices=list(images_mod.QUALITIES))

    add_common(sub.add_parser("preview", help="生成预览 HTML"))
    add_common(sub.add_parser("voice", help="只做诊断与定点重写，不排版落盘"))
    add_common(sub.add_parser("draft", help="写入草稿箱"), draft=True)

    sp = sub.add_parser("update", help="更新已有草稿")
    sp.add_argument("--media-id", required=True)
    add_common(sp, draft=True)

    sp = sub.add_parser("status", help="查看草稿状态")
    sp.add_argument("--media-id", required=True)

    return p


# ------------------------------------------------------------------ 命令
def cmd_init(a) -> int:
    if a.template:
        path = Path(a.out).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(profile_mod.template(), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return out({
            "ok": True,
            "profile_path": str(path),
            "mode": "template",
            "next": "按注释填好，然后 preview 时会自动读取；也可 --profile 指定",
        })

    if a.answers:
        answers = json.loads(Path(a.answers).read_text(encoding="utf-8"))
        prof = profile_mod.from_answers(answers)
        path = profile_mod.save(prof, a.out)
        return out({
            "ok": True,
            "profile_path": str(path),
            "mode": "questionnaire",
            "fields_filled": _count_fields(prof),
            "preview": profile_mod.contract(prof),
        })

    # 无参数：把问卷交给 agent，由它在对话里问
    return out({**profile_mod.questions_payload(), "target_path": str(Path(a.out).expanduser())})


def _count_fields(p: dict) -> int:
    n = 0
    for sec in p.values():
        if isinstance(sec, dict):
            for v in sec.values():
                if v not in ("", [], {}, None):
                    n += 1
        elif sec not in ("", [], None):
            n += 1
    return n


def cmd_check(a) -> int:
    try:
        client = wx.from_env()
    except wx.WxError as e:
        return out(e.payload(), EXIT["cred"])
    res = client.check()
    if not res.get("ok"):
        return out(res, res.get("errcode") == 40164 and EXIT["ip"] or EXIT["cred"])
    hints = []
    if not res.get("ip_ok"):
        hints.append("IP 未加白，上传会全失败")
    res["hints"] = hints
    res["note"] = "凭据可用。若后续 uploadimg 报 40164，把出口 IP 加进白名单。"
    return out(res)


def cmd_qc(a) -> int:
    paths = pipeline.resolve_images(a.images)
    res = images_mod.qc(paths, a.quality)
    return out(res, 0 if res["ok"] else EXIT["image"])


def _load_profile(a) -> dict:
    path, source = profile_mod.find(
        getattr(a, "profile", None),
        str(Path(a.text_file).parent) if getattr(a, "text_file", None) else None,
    )
    if not path:
        return {"identity": {"name": "作者"}, "_meta": {"source": "none"}, "voice": {},
                "topics": {}, "typesetting": {}, "taboo": {}, "family": {"members": []}}
    prof = profile_mod.load(path)
    prof["_meta"]["source"] = f"{source}: {path}"
    return prof


def _inputs(a) -> tuple[str, list[str]]:
    if getattr(a, "post", None):
        post = pipeline.load_post(a.post)
        return post.get("text", ""), post.get("images") or []
    text = pipeline.read_text(a.text, a.text_file, None)
    paths = pipeline.resolve_images(a.images)
    return text, paths


def cmd_preview(a) -> int:
    prof = _load_profile(a)
    text, paths = _inputs(a)
    res = pipeline.preview(
        text=text, image_paths=paths, scene=a.scene, profile=prof,
        quality=a.quality, rewrite=a.rewrite, workdir=a.workdir,
        do_voice=not a.no_voice, max_rounds=a.max_rounds,
    )
    res.pop("doc", None)
    res["note"] = "把 preview_path 给用户看，等确认版式再 draft"
    return out(res)


def cmd_voice(a) -> int:
    prof = _load_profile(a)
    text, paths = _inputs(a)
    built = pipeline.build(text=text, image_paths=paths, scene=a.scene,
                           profile=prof, rewrite=a.rewrite)
    diag = voice.diagnose(built["doc"], prof, a.scene)
    rw = None
    if not a.no_voice and diag["recommend"] == "rewrite":
        if llm.available():
            rw = pipeline.rewrite_mod.run(built["doc"], prof, llm.complete, a.scene, a.max_rounds)
        else:
            built["warnings"].append(
                "检测到需要重写，但未配置 LLM_API_KEY；issues 已列出，可让用户自行改这几句"
            )
    return out({
        "ok": True,
        "scores": diag["scores"],
        "recommend": diag["recommend"],
        "issues": diag["issues"],
        "keep": diag["keep"],
        "positive": diag["positive"],
        "stats": diag["stats"],
        "rewrite": rw["summary"] if rw else None,
        "changes": rw["changes"] if rw else [],
        "warnings": built["warnings"],
    })


def cmd_draft(a) -> int:
    prof = _load_profile(a)
    text, paths = _inputs(a)
    res = pipeline.draft(
        text=text, image_paths=paths, scene=a.scene, profile=prof,
        quality=a.quality, rewrite=a.rewrite, workdir=a.workdir,
        cover=a.cover, force_new=a.force_new, media_id=getattr(a, "media_id", None),
        do_voice=not a.no_voice, max_rounds=a.max_rounds,
    )
    bad = [k for k, v in (res.get("checks") or {}).items() if v is False]
    if bad:
        res["ok"] = False
        res["mismatch"] = bad
        return out(res, EXIT["readback"])
    return out(res)


def cmd_status(a) -> int:
    return out(pipeline.status(a.media_id))


ROUTES = {
    "init": cmd_init,
    "check": cmd_check,
    "qc": cmd_qc,
    "preview": cmd_preview,
    "voice": cmd_voice,
    "draft": cmd_draft,
    "update": cmd_draft,
    "status": cmd_status,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return ROUTES[args.cmd](args)
    except profile_mod.ProfileError as e:
        return out({"ok": False, "error": "人格文件非法", "details": e.errors}, EXIT["profile"])
    except wx.WxError as e:
        return out(e.payload(), e.exit_code)
    except pipeline.PipelineError as e:
        payload = {"ok": False, "error": str(e), **e.payload}
        return out(payload, e.exit_code)
    except FileNotFoundError as e:
        return out({"ok": False, "error": f"文件不存在：{e}"}, EXIT["args"])
    except KeyboardInterrupt:
        return out({"ok": False, "error": "已中断"}, 130)
    except Exception as e:  # 兜底：给出可读错误，但保留栈到 stderr
        log(traceback.format_exc())
        return out({"ok": False, "error": f"{type(e).__name__}: {e}"}, 1)


if __name__ == "__main__":
    raise SystemExit(main())
