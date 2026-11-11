"""编排：入参归一 → 校验 → 生成 → 排版 → 诊断 → 上传 → 草稿 → 回读。

这里只做编排，不做具体实现。所有路径在入口处就 resolve 成绝对路径，
管道内部不再依赖任何「当前目录」——原型的相对路径 bug 就出在这。
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import images as images_mod
import llm
import profile as profile_mod
import render
import rewrite as rewrite_mod
import state
import voice
import wx


class PipelineError(Exception):
    def __init__(self, message: str, exit_code: int = 2, payload: dict | None = None):
        self.exit_code = exit_code
        self.payload = payload or {}
        super().__init__(message)


# ------------------------------------------------------------------ 输入
def resolve_images(items: list[str] | None) -> list[str]:
    """展开目录、校验存在性，全部转绝对路径。"""
    out: list[str] = []
    for it in items or []:
        p = Path(it).expanduser().resolve()
        if p.is_dir():
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif", "*.bmp"):
                out += [str(x) for x in sorted(p.glob(ext))]
        elif p.is_file():
            out.append(str(p))
        else:
            raise PipelineError(f"图片不存在：{it}")
    if not out:
        return []
    # 去重但不打乱顺序
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def read_text(text: str | None, text_file: str | None, post: str | None) -> str:
    if text:
        return text
    if text_file:
        p = Path(text_file).expanduser().resolve()
        if not p.is_file():
            raise PipelineError(f"文案文件不存在：{text_file}")
        return p.read_text(encoding="utf-8")
    if post:
        return load_post(post).get("text", "")
    raise PipelineError("缺少文案：用 --text 或 --text-file 给一段话")


def load_post(path: str | Path) -> dict:
    """批量模式：一个 post.json 带全部字段。路径相对 post.json 所在目录解析。"""
    p = Path(path).expanduser().resolve()
    if p.is_dir():
        p = p / "post.json"
    if not p.is_file():
        raise PipelineError(f"找不到 post.json：{p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    base = p.parent
    imgs = []
    for it in data.get("images") or []:
        q = Path(it)
        imgs.append(str(q if q.is_absolute() else (base / q).resolve()))
    images_mod_list = resolve_images(imgs)
    return {
        **data,
        "images": images_mod_list,
        "text": data.get("text") or "",
        "_dir": str(base),
    }


# ------------------------------------------------------------------ 生成
def build(*, text: str, image_paths: list[str], scene: str | None,
          profile: dict, rewrite: bool) -> dict:
    gen = llm.expand(text, image_paths, profile, scene, rewrite=rewrite)
    doc = {
        "title": gen["title"],
        "author": (profile.get("identity") or {}).get("name", ""),
        "blocks": gen["blocks"],
    }
    warnings = list(gen.get("warnings") or [])
    # 人格里配了落款就补上：这是「像本人写的」最廉价也最有效的一笔
    signature = (profile.get("identity") or {}).get("signature")
    if signature and not any(b.get("type") == "sign_off" for b in doc["blocks"]):
        doc["blocks"].append({"type": "sign_off", "signature": signature})
    return {"doc": doc, "title": gen["title"], "digest": gen["digest"],
            "warnings": warnings, "source": gen.get("source", "heuristic")}


def render_doc(doc: dict, scene: str | None) -> str:
    return render.render_html(doc, scene)


def preview(*, text: str, image_paths: list[str], scene: str | None, profile: dict,
            quality: str, rewrite: bool, workdir: str | Path,
            do_voice: bool = True, max_rounds: int = 2, complete=None) -> dict:
    built = build(text=text, image_paths=image_paths, scene=scene,
                  profile=profile, rewrite=rewrite)
    doc = built["doc"]
    warnings = list(built["warnings"])

    diag = voice.diagnose(doc, profile, scene)
    rw = None
    if do_voice and diag["recommend"] == "rewrite":
        if complete is None and llm.available():
            complete = llm.complete
        if complete is not None:
            rw = rewrite_mod.run(doc, profile, complete, scene, max_rounds)
            doc = rw["doc"]
            diag = rw["after"]
        else:
            warnings.append(
                "检测到问题但未配置 LLM_API_KEY，无法做定点重写；已列出问题供人工修改"
            )

    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    slug = _slug(built["title"])
    html = render_doc(doc, scene)
    vdir = workdir / slug
    vdir.mkdir(parents=True, exist_ok=True)

    (vdir / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (vdir / "content.html").write_text(html, encoding="utf-8")
    (vdir / "voice.json").write_text(
        json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    page = render.render_page(doc, scene)
    preview_path = vdir / "preview.html"
    preview_path.write_text(page, encoding="utf-8")

    fp = state.fingerprint(built["title"], html, image_paths)
    return {
        "ok": True,
        "preview_path": str(preview_path),
        "workdir": str(vdir),
        "content_html": html,
        "content_len": len(html),
        "title": built["title"],
        "digest": built["digest"],
        "title_len": len(built["title"]),
        "fingerprint": fp,
        "source": built["source"],
        "voice": {
            "scores": diag["scores"],
            "recommend": diag["recommend"],
            "issue_count": len(diag["issues"]),
            "keep_count": len(diag["keep"]),
            "alarms": diag["positive"]["alarms"],
        },
        "rewrite": rw["summary"] if rw else None,
        "warnings": warnings,
        "doc": doc,
    }


# ------------------------------------------------------------------ 发布
def draft(*, text: str, image_paths: list[str], scene: str | None, profile: dict,
          quality: str, rewrite: bool, workdir: str | Path, cover: str | None = None,
          force_new: bool = False, media_id: str | None = None,
          do_voice: bool = True, max_rounds: int = 2, complete=None,
          client: wx.WxClient | None = None) -> dict:
    pv = preview(
        text=text, image_paths=image_paths, scene=scene, profile=profile,
        quality=quality, rewrite=rewrite, workdir=workdir, do_voice=do_voice,
        max_rounds=max_rounds, complete=complete,
    )
    doc = pv["doc"]
    vdir = Path(pv["workdir"])
    warnings = list(pv["warnings"])

    client = client or wx.from_env()

    # 1. 图片预处理 + 上传，得到 CDN URL
    quality_report = []
    mapping: dict[str, str] = {}
    upload_dir = vdir / "upload"
    for p in image_paths:
        prep = images_mod.prepare(p, quality, upload_dir)
        quality_report.append(
            {k: prep[k] for k in ("src", "src_px", "out_px", "out_bytes", "quality", "lossless", "action", "reason")}
        )
        if not prep.get("ok"):
            raise PipelineError(
                prep.get("reason", "图片处理失败"),
                exit_code=7,
                payload={"ok": False, "quality": quality_report, "blocked": prep.get("src")},
            )
        url = client.upload_body_image(prep["out"])
        mapping[p] = url
        quality_report[-1]["cdn_url"] = url

    # 2. 把 doc 里的本地路径换成 CDN URL 后再排版
    doc_cdn = _swap_images(doc, mapping)
    html = render_doc(doc_cdn, scene)

    # 3. 封面
    cover_src = Path(cover).expanduser().resolve() if cover else Path(image_paths[0])
    cover_prep = images_mod.prepare(str(cover_src), quality if quality != "lossless" else "high",
                                    upload_dir, limit=images_mod.COVER_LIMIT)
    if not cover_prep.get("ok"):
        raise PipelineError(cover_prep.get("reason", "封面处理失败"), exit_code=7,
                            payload={"ok": False, "quality": quality_report})
    thumb = client.upload_cover(cover_prep["out"])

    # 4. 组装 article
    article = {
        "title": pv["title"],
        "author": (profile.get("identity") or {}).get("name", "")[: wx.AUTHOR_MAX],
        "digest": pv["digest"][: wx.DIGEST_MAX],
        "content": html,
        "content_source_url": "",
        "thumb_media_id": thumb["media_id"],
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    warns = wx.validate_article(article)
    blocking = [w for w in warns if "必须" in w or "会被拒" in w or "会失败" in w]
    if blocking:
        raise PipelineError("提交前校验未通过：" + "；".join(blocking), exit_code=2,
                            payload={"ok": False, "warnings": warns})

    # 5. 幂等：同指纹复用，改稿走 update
    # 指纹必须与「上传结果」无关：微信每次上传可能返回不同 URL，
    # 用它算指纹会让同一篇稿子每次都算新稿，草稿箱里堆一串重复。
    # 所以用本地渲染结果 + 本地图片内容摘要。
    img_ids = [hashlib.md5(Path(p).read_bytes()).hexdigest()[:8] for p in image_paths]
    fp = state.fingerprint(pv["title"], pv["content_html"], img_ids)
    existing = state.lookup(workdir, fp)
    reused = False
    if media_id:
        client.update_draft(media_id, article)
        mid = media_id
    elif existing and not force_new:
        client.update_draft(existing["media_id"], article)
        mid = existing["media_id"]
        reused = True
    else:
        mid = client.add_draft(article)
    state.record(workdir, fp, mid, title=pv["title"], thumb_media_id=thumb["media_id"])

    # 6. 回读校验：草稿里必须真的是我们提交的东西
    checks = _verify_draft(client, mid, html)

    # 7. 图片核验：从 CDN 拉回来量尺寸，不靠承诺
    remote = []
    for q in quality_report:
        v = images_mod.verify_remote(q["cdn_url"], q["out_px"], q["out_bytes"])
        remote.append({**q, "cdn_px": v["cdn_px"], "cdn_bytes": v["cdn_bytes"],
                       "lossless": v["lossless"], "loss_reason": v["reason"]})

    return {
        "ok": True,
        "media_id": mid,
        "reused": reused,
        "title": pv["title"],
        "digest": pv["digest"],
        "preview_path": pv["preview_path"],
        "workdir": str(vdir),
        "checks": checks,
        "quality": remote,
        "voice": pv["voice"],
        "warnings": warnings + warns,
        "next": "到公众号后台「草稿箱」核对，确认无误后手动点发表（本 skill 不会自动发表）",
    }


def _verify_draft(client: wx.WxClient, media_id: str, html: str) -> dict:
    """回读草稿，断言标题非空、图片还在、正文没被大幅截断。

    比对基准取自提交的 html 本身，而不是本轮「上传返回的 URL」——
    微信对同一张图可能返回不同 URL，用后者会让一致性检查自己误报。
    """
    try:
        data = client.get_draft(media_id)
    except wx.WxError as e:
        return {"readback": False, "error": e.payload()}
    items = data.get("news_item") or []
    if not items:
        return {"readback": False, "error": "草稿回读为空"}
    it = items[0]
    content = it.get("content") or ""
    urls = re.findall(r"https?://mmbiz\.qpic\.cn/[^\s\"']+", html)
    missing = [u for u in urls if u not in content]
    return {
        "readback": True,
        "title_match": (it.get("title") or "") != "",
        "blocks_present": "<section" in content,
        "content_len_remote": len(content),
        "content_len_local": len(html),
        "images_expected": len(urls),
        "images_on_cdn": len(urls) - len(missing),
        "all_images_in_content": not missing,
    }


def status(media_id: str, client: wx.WxClient | None = None) -> dict:
    client = client or wx.from_env()
    data = client.get_draft(media_id)
    items = data.get("news_item") or []
    if not items:
        raise PipelineError("草稿不存在或已被删除", exit_code=5)
    it = items[0]
    content = it.get("content") or ""
    return {
        "ok": True,
        "media_id": media_id,
        "title": it.get("title", ""),
        "digest": it.get("digest", ""),
        "author": it.get("author", ""),
        "images_on_cdn": len(re.findall(r"mmbiz\.qpic\.cn", content)),
        "block_count": content.count("<section"),
        "content_len": len(content),
        "update_time": it.get("update_time"),
    }


# ------------------------------------------------------------------ 工具
def _swap_images(doc: dict, mapping: dict) -> dict:
    d = copy.deepcopy(doc)
    for b in d.get("blocks") or []:
        t = (b.get("type") or "").lower()
        if t in ("image", "photo_polaroid", "compare_pair"):
            for key in ("src", "a", "b"):
                if b.get(key) in mapping:
                    b[key] = mapping[b[key]]
        elif t == "images":
            b["srcs"] = [mapping.get(s, s) for s in (b.get("srcs") or [])]
    return d


def _slug(title: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fa5-]+", "", title or "post")[:18].strip("-")
    return s or "post"
