"""WeChat draft delivery with post-upload evidence.

The only network boundary in this skill.  Credentials come from arguments,
``WECHAT_APPID`` / ``WECHAT_APPSECRET``, or a local config file.  Every uploaded
body image is downloaded again and compared with the prepared file; the report
says ``lossless: false`` whenever pixels changed.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any
import urllib.error
import urllib.parse
import urllib.request
import uuid

import images
import render

API = "https://api.weixin.qq.com/cgi-bin/"
BACKEND = "https://mp.weixin.qq.com/"
CONFIG = Path.home() / ".config/workbuddy-wechat/config.json"
MAX_CONTENT = 1024 * 1024


class WechatError(RuntimeError):
    def __init__(self, message: str, code: int | None = None, ambiguous: bool = False):
        super().__init__(message)
        self.code = code
        self.ambiguous = ambiguous


class ConfigError(ValueError):
    pass


def credentials(appid: str | None = None, secret: str | None = None) -> tuple[str, str]:
    env_appid = os.environ.get("WECHAT_APPID", "").strip()
    env_secret = os.environ.get("WECHAT_APPSECRET", "").strip()
    config: dict[str, Any] = {}
    if CONFIG.is_file() and (not (appid or env_appid) or not (secret or env_secret)):
        try:
            config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise ConfigError(f"公众号本机配置无法读取：{error}") from error
    chosen_appid = (appid or env_appid or (config.get("appid") if isinstance(config.get("appid"), str) else "") or "").strip()
    chosen_secret = (secret or env_secret or (config.get("secret") if isinstance(config.get("secret"), str) else "") or "").strip()
    if not chosen_appid or not chosen_secret:
        raise ConfigError("请配置公众号 AppID 和 AppSecret（参数、环境变量或本机 config.json）。")
    return chosen_appid, chosen_secret


def _request_json(path: str, payload: dict[str, Any], token: str | None = None, timeout: int = 30) -> dict[str, Any]:
    url = urllib.parse.urljoin(API, path)
    if token:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"access_token": token})
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        raise WechatError(f"{path} 返回 HTTP {error.code}", None, True) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise WechatError(f"{path} 请求中断或超时：{error}", None, True) from error
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WechatError(f"{path} 返回无法解析的响应", None, True) from error
    if not isinstance(result, dict):
        raise WechatError(f"{path} 返回异常响应", None, True)
    code = result.get("errcode", 0)
    if code not in (0, None):
        raise WechatError(f"{path} 微信错误 {code} {result.get('errmsg', '')}", int(code), code == -1)
    return result


def _request_form(path: str, file_path: Path, token: str, extra: dict[str, str] | None = None) -> dict[str, Any]:
    data = file_path.read_bytes()
    suffix = file_path.suffix.lower()
    content_type = "image/png" if suffix == ".png" else "image/jpeg"
    boundary = "----workbuddy" + uuid.uuid4().hex
    parts: list[bytes] = []
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="image{suffix}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
    )
    parts.append(data)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    url = urllib.parse.urljoin(API, path)
    query = {"access_token": token, **(extra or {})}
    url += ("&" if "?" in url else "?") + urllib.parse.urlencode(query)
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        raise WechatError(f"{path} 返回 HTTP {error.code}", None, True) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise WechatError(f"{path} 请求中断或超时：{error}", None, True) from error
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WechatError(f"{path} 返回无法解析的响应", None, True) from error
    if not isinstance(result, dict):
        raise WechatError(f"{path} 返回异常响应", None, True)
    code = result.get("errcode", 0)
    if code not in (0, None):
        raise WechatError(f"{path} 微信错误 {code} {result.get('errmsg', '')}", int(code), code == -1)
    return result


def stable_token(appid: str, secret: str) -> str:
    result = _request_json(
        "stable_token",
        {"grant_type": "client_credential", "appid": appid, "secret": secret, "force_refresh": False},
    )
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise WechatError("微信未返回 access_token", None, False)
    return token


def upload_body(token: str, prepared: Path) -> str:
    result = _request_form("media/uploadimg", prepared, token)
    url = result.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise WechatError("微信未返回正文图片 URL", None, True)
    return url


def upload_cover(token: str, prepared: Path) -> tuple[str, str | None]:
    result = _request_form("material/add_material", prepared, token, {"type": "image"})
    media_id = result.get("media_id")
    if not isinstance(media_id, str) or not media_id:
        raise WechatError("微信未返回封面 media_id", None, True)
    url = result.get("url")
    return media_id, url if isinstance(url, str) else None


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 WorkBuddy-Wechat-Article"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(20 * 1024 * 1024)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise WechatError(f"回读图片失败：{error}", None, True) from error
    if not data:
        raise WechatError("回读图片为空", None, True)
    target.write_bytes(data)


def confirm_code(account: str, action: str, version: str) -> str:
    return hashlib.sha256(f"{account}|{action}|{version}".encode("utf-8")).hexdigest()[:12]


def bundle_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": bundle.get("title", ""),
        "digest": bundle.get("digest", ""),
        "author": bundle.get("author", ""),
        "scene": bundle.get("scene", ""),
        "quality": bundle.get("quality", ""),
        "typesetting": bundle.get("typesetting", {}),
        "blocks": bundle.get("blocks", []),
        "images": [(item.get("src", ""), item.get("sha256", "")) for item in bundle.get("images", [])],
        "cover": (bundle.get("cover") or {}).get("sha256", ""),
    }


def bundle_version(bundle: dict[str, Any]) -> str:
    data = json.dumps(bundle_payload(bundle), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def load_bundle(workdir: str | Path) -> tuple[dict[str, Any], Path]:
    root = Path(workdir).expanduser().resolve()
    path = root / "bundle.json"
    if not path.is_file():
        raise ConfigError("文章目录中没有 bundle.json，请先运行 preview。")
    try:
        bundle = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"bundle.json 无法读取：{error}") from error
    if not isinstance(bundle, dict) or bundle.get("schema") != 1:
        raise ConfigError("bundle.json 不是当前版本的预览包。")
    if not isinstance(bundle.get("blocks"), list) or not isinstance(bundle.get("images", []), list):
        raise ConfigError("预览包的 blocks 或 images 结构无效。")
    if not isinstance(bundle.get("cover", {}), dict):
        raise ConfigError("预览包的封面结构无效。")
    if bundle.get("version") != bundle_version(bundle):
        raise ConfigError("预览包内容与版本号不一致，请重新生成预览。")
    for item in list(bundle.get("images", [])) + [bundle.get("cover") or {}]:
        if not item:
            continue
        relative = item.get("path")
        if not isinstance(relative, str):
            raise ConfigError("预览包缺少图片路径。")
        file = (root / relative).resolve()
        if root not in file.parents and file != root:
            raise ConfigError("预览包图片路径越界。")
        if not file.is_file():
            raise ConfigError(f"预览图片缺失：{relative}")
        if hashlib.sha256(file.read_bytes()).hexdigest() != item.get("sha256"):
            raise ConfigError(f"预览图片已改变：{relative}，请重新生成预览。")
    return bundle, root


def _verify_remote(prepared: Path, url: str, root: Path) -> dict[str, Any]:
    scratch = Path(tempfile.mkdtemp(prefix="workbuddy-remote-"))
    downloaded = scratch / "remote.bin"
    try:
        download(url, downloaded)
        result = images.verify(prepared, downloaded)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    result["cdn_url"] = url
    return result


def _render_final(bundle: dict[str, Any], mapping: dict[str, str]) -> tuple[str, list[str]]:
    article, warnings, _ = render.render_article(
        {"blocks": bundle["blocks"], "title": bundle.get("title", ""), "scene": bundle.get("scene", "")},
        mapping,
        bundle.get("scene"),
        {"typesetting": bundle.get("typesetting", {})},
    )
    if len(article.encode("utf-8")) >= MAX_CONTENT:
        raise ConfigError("正文 HTML 超过微信 1 MiB 限制，请减少装饰或图片。")
    return article, warnings


def draft(
    workdir: str | Path,
    account: str,
    action: str,
    confirmed: str,
    *,
    media_id: str | None = None,
    appid: str | None = None,
    secret: str | None = None,
    verify: bool = True,
) -> dict[str, Any]:
    if action not in {"draft", "update"}:
        raise ConfigError("action 可选 draft 或 update")
    if action == "update" and not media_id:
        raise ConfigError("更新草稿需要 --media-id")
    bundle, root = load_bundle(workdir)
    expected = confirm_code(account, action, bundle["version"])
    if confirmed != expected:
        raise ConfigError("确认码与当前预览、账号或操作不匹配，请重新确认。")
    chosen_appid, chosen_secret = credentials(appid, secret)
    if chosen_appid != account:
        raise ConfigError("目标账号与本机凭据不一致。")
    token = stable_token(chosen_appid, chosen_secret)
    quality: list[dict[str, Any]] = []
    mapping: dict[str, str] = {}
    try:
        for item in bundle.get("images", []):
            prepared = (root / item["path"]).resolve()
            url = upload_body(token, prepared)
            mapping[item["src"]] = url
            evidence: dict[str, Any] = {
                "src": item["src"],
                "prepared": item["path"],
                "src_px": item["measurement"].get("src_px"),
                "prepared_px": item["measurement"].get("output_px"),
                "src_bytes": item["measurement"].get("src_bytes"),
                "prepared_bytes": item["measurement"].get("output_bytes"),
                "lossless": False,
                "cdn_px": None,
                "cdn_bytes": None,
                "reason": item["measurement"].get("reason"),
                "cdn_url": url,
            }
            if verify:
                checked = _verify_remote(prepared, url, root)
                evidence.update(
                    {
                        "cdn_px": checked.get("remote_px"),
                        "cdn_bytes": checked.get("remote_bytes"),
                        "lossless": bool(checked.get("lossless"))
                        and item["measurement"].get("quality") == "lossless",
                        "reason": checked.get("reason") or item["measurement"].get("reason"),
                    }
                )
            else:
                evidence["reason"] = "未回读核验；lossless 一律记为 false"
            if not evidence["lossless"] and not evidence["reason"]:
                evidence["reason"] = "该档不是 lossless，或远端像素未保持一致"
            quality.append(evidence)

        cover_item = bundle.get("cover") or {}
        if not cover_item:
            raise ConfigError("预览包缺少封面。")
        cover_path = (root / cover_item["path"]).resolve()
        cover_id, cover_url = upload_cover(token, cover_path)
        cover_evidence = {
            "src": cover_item.get("src"),
            "prepared": cover_item["path"],
            "media_id": cover_id,
            "cdn_url": cover_url,
            "lossless": False,
            "reason": cover_item.get("measurement", {}).get("reason"),
        }
        if verify and cover_url:
            checked = _verify_remote(cover_path, cover_url, root)
            cover_evidence.update(
                {
                    "cdn_px": checked.get("remote_px"),
                    "cdn_bytes": checked.get("remote_bytes"),
                    "lossless": bool(checked.get("lossless"))
                    and cover_item.get("measurement", {}).get("quality") == "lossless",
                    "reason": checked.get("reason") or cover_item.get("measurement", {}).get("reason"),
                }
            )
        if not cover_evidence["lossless"] and not cover_evidence.get("reason"):
            cover_evidence["reason"] = "封面未回读，或该档不是 lossless，或远端像素未保持一致"

        content, warnings = _render_final(bundle, mapping)
        article = {
            "title": bundle.get("title", ""),
            "author": bundle.get("author", ""),
            "digest": bundle.get("digest", ""),
            "content": content,
            "thumb_media_id": cover_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }
        if action == "draft":
            result = _request_json("draft/add", {"articles": [article]}, token)
            created_id = result.get("media_id")
            if not isinstance(created_id, str) or not created_id:
                raise WechatError("微信未返回草稿 media_id", None, True)
        else:
            result = _request_json(
                "draft/update", {"media_id": media_id, "index": 0, "articles": article}, token
            )
            created_id = media_id or ""
            if result.get("errcode") not in (0, None):
                raise WechatError("微信未确认草稿更新", None, True)

        readback: dict[str, Any] = {"ok": False}
        try:
            stored = _request_json("draft/get", {"media_id": created_id}, token)
            news = stored.get("news_item")
            if isinstance(news, list) and news and isinstance(news[0], dict):
                item = news[0]
                readback = {
                    "ok": True,
                    "title": item.get("title"),
                    "title_matches": item.get("title") == article["title"],
                    "content_chars": len(str(item.get("content", ""))),
                    "thumb_media_id": item.get("thumb_media_id"),
                    "thumb_matches": item.get("thumb_media_id") == cover_id,
                }
        except WechatError as error:
            readback = {"ok": False, "error": str(error)}

        return {
            "ok": True,
            "action": action,
            "media_id": created_id,
            "account": account,
            "title": article["title"],
            "backend": BACKEND,
            "quality": quality,
            "cover": cover_evidence,
            "warnings": warnings,
            "draft_readback": readback,
            "confirmed": expected,
        }
    except WechatError as error:
        raise error
