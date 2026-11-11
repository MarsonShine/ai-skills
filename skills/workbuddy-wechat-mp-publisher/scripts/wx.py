"""微信公众号接口封装：只做「写进草稿箱」，永不发表。

几条硬规矩：
1. 只用 stable_token。普通 token 在多进程下会互相踢，表现为随机 40001。
2. secret 与 token 全程打码，不进日志、不进产物、不进错误信息。
3. 40164（IP 不在白名单）单独识别：把微信返回里的出口 IP 抠出来告诉用户，
   否则这个错误看起来像「鉴权失败」，能卡人半小时。
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

API = "https://api.weixin.qq.com"
TOKEN_URL = f"{API}/cgi-bin/stable_token"

TITLE_HARD = 64     # 微信标题上限（字符）
TITLE_WARN = 32     # 超过这个长度，列表页会被截断
DIGEST_MAX = 120
AUTHOR_MAX = 16
CONTENT_MAX = 20000

ERR_HINT = {
    -3: ("缺少凭据", "设置 WX_APPID / WX_SECRET 环境变量，或写入 ~/.config/wechat-mp/config.json（0600）。"),
    -2: ("图片超过接口上限", "正文图上限 1MB，封面 10MB。用 --quality 换档或换图。"),
    -1: ("返回格式异常", "微信返回的不是 JSON，通常是网关错误或被代理拦截。"),
    40001: ("凭据失效", "AppSecret 不对，或 token 被别处刷新了。检查 WX_SECRET。"),
    40007: ("media_id 非法", "缩略图或草稿的 media_id 不存在，可能已被删除。"),
    40008: ("参数类型错误", "常见于标题超长或字段类型不对。检查标题长度与字段类型。"),
    40013: ("AppID 非法", "检查 WX_APPID 是否抄错。"),
    40125: ("AppSecret 无效", "去后台重置 AppSecret，注意别带空格。"),
    40164: ("IP 不在白名单", "把下面回显的出口 IP 加进「设置与开发 → 基本配置 → IP 白名单」。"),
    45009: ("接口调用超限", "当日额度用完。草稿/上传接口有每日上限，明天再试。"),
    48001: ("接口未授权", "账号类型不支持该接口。未认证订阅号不能调 freepublish，但草稿箱可以用。"),
    53404: ("草稿数量超限", "草稿箱有上限，先删旧草稿。"),
}


class WxError(Exception):
    def __init__(self, code: int, msg: str, api: str = ""):
        self.code = code
        self.msg = msg
        self.api = api
        self.ip = _extract_ip(msg)
        hint = ERR_HINT.get(code)
        self.title = hint[0] if hint else "微信接口返回错误"
        self.hint = hint[1] if hint else "看 errcode/errmsg 原文判断。"
        super().__init__(f"[{code}] {msg}")

    @property
    def exit_code(self) -> int:
        if self.code == 40164:
            return 4
        if self.code in (-3, 40001, 40013, 40125):
            return 3
        if self.code == -2:
            return 7
        return 5

    def payload(self) -> dict:
        out = {
            "ok": False,
            "errcode": self.code,
            "errmsg": self.msg,
            "title": self.title,
            "hint": self.hint,
            "api": self.api,
        }
        if self.ip:
            out["exit_ip"] = self.ip
            out["hint"] = f"把出口 IP {self.ip} 加入公众号 IP 白名单后重试。"
        return out


def _extract_ip(msg: str) -> str:
    m = re.search(r"invalid ip ([0-9a-fA-F:.]+)", msg or "")
    return m.group(1) if m else ""


class WxClient:
    def __init__(self, appid: str, secret: str, cache: str | Path | None = None):
        self.appid = appid
        self._secret = secret
        self.cache = Path(
            cache or os.environ.get("WX_TOKEN_CACHE") or "~/.cache/wagent/token.json"
        ).expanduser()
        self._token = ""
        self._exp = 0.0

    # -------------------------------------------------------------- 凭据
    @property
    def masked(self) -> dict:
        return {
            "appid": self.appid[:6] + "…" + self.appid[-2:] if len(self.appid) > 8 else "…",
            "secret": "已配置" if self._secret else "缺失",
        }

    def token(self, force: bool = False) -> str:
        if not force:
            if self._token and time.time() < self._exp - 60:
                return self._token
            cached = self._read_cache()
            if cached:
                self._token, self._exp = cached
                return self._token
        if requests is None:
            raise RuntimeError("缺少 requests，请 pip install requests")
        r = requests.post(
            TOKEN_URL,
            json={
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self._secret,
                "force_refresh": bool(force),
            },
            timeout=20,
        )
        data = r.json()
        if data.get("errcode"):
            raise WxError(data["errcode"], data.get("errmsg", ""), "stable_token")
        self._token = data["access_token"]
        self._exp = time.time() + int(data.get("expires_in", 7200))
        self._write_cache()
        return self._token

    def _read_cache(self):
        try:
            d = json.loads(self.cache.read_text())
            if d.get("appid") == self.appid and d.get("expires_at", 0) > time.time() + 120:
                return d["token"], d["expires_at"]
        except Exception:
            pass
        return None

    def _write_cache(self):
        try:
            self.cache.parent.mkdir(parents=True, exist_ok=True)
            self.cache.write_text(
                json.dumps(
                    {"appid": self.appid, "token": self._token, "expires_at": self._exp}
                )
            )
            self.cache.chmod(0o600)
        except OSError:
            pass  # 缓存写不了不影响主流程

    # -------------------------------------------------------------- 请求
    def _post(self, path: str, *, params: dict | None = None, json_body: dict | None = None,
              files=None, retry: bool = True):
        url = f"{API}{path}"
        p = {"access_token": self.token()}
        p.update(params or {})
        r = requests.post(url, params=p, json=json_body, files=files, timeout=60)
        try:
            data = r.json()
        except ValueError:
            raise WxError(-1, f"返回不是 JSON：{r.text[:200]}", path) from None
        code = data.get("errcode")
        if code in (40001, 42001) and retry:
            # token 被别处刷新：强刷一次再试
            self.token(force=True)
            return self._post(path, params=params, json_body=json_body, files=files, retry=False)
        if code:
            raise WxError(code, data.get("errmsg", ""), path)
        return data

    # -------------------------------------------------------------- 图片
    def upload_body_image(self, path: str | Path) -> str:
        """正文图，返回可直接放进 <img src> 的 URL。上限 1MB。"""
        p = Path(path)
        size = p.stat().st_size
        if size > 1_048_576:
            raise WxError(-2, f"{p.name} 有 {size / 1048576:.1f}MB，超过正文图 1MB 上限", "uploadimg")
        with p.open("rb") as f:
            data = self._post(
                "/cgi-bin/media/uploadimg",
                files={"media": (p.name, f, _mime(p))},
            )
        return data["url"]

    def upload_cover(self, path: str | Path) -> dict:
        """封面图，返回 media_id（草稿必需）与 url。上限 10MB。"""
        p = Path(path)
        with p.open("rb") as f:
            data = self._post(
                "/cgi-bin/material/add_material",
                params={"type": "image"},
                files={"media": (p.name, f, _mime(p))},
            )
        return {"media_id": data["media_id"], "url": data.get("url", "")}

    # -------------------------------------------------------------- 草稿
    def add_draft(self, article: dict) -> str:
        data = self._post("/cgi-bin/draft/add", json_body={"articles": [article]})
        return data["media_id"]

    def update_draft(self, media_id: str, article: dict, index: int = 0) -> dict:
        return self._post(
            "/cgi-bin/draft/update",
            json_body={"media_id": media_id, "index": index, "articles": article},
        )

    def get_draft(self, media_id: str) -> dict:
        return self._post("/cgi-bin/draft/get", json_body={"media_id": media_id})

    def delete_draft(self, media_id: str) -> dict:
        return self._post("/cgi-bin/draft/delete", json_body={"media_id": media_id})

    # -------------------------------------------------------------- 自检
    def check(self) -> dict:
        """只验凭据与网络。IP 未加白时这里就会暴露，不必等到上传。"""
        out = {"ok": True, "appid_masked": self.masked["appid"], "ip_ok": True}
        try:
            tok = self.token()
            out["token_ok"] = True
            out["token_len"] = len(tok)
            out["token_cached"] = self.cache.exists()
        except WxError as e:
            out.update(e.payload())
            out["token_ok"] = False
            out["ip_ok"] = e.code != 40164
            return out
        return out


def _mime(p: Path) -> str:
    ext = p.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def from_env() -> "WxClient":
    appid = os.environ.get("WX_APPID") or ""
    secret = os.environ.get("WX_SECRET") or ""
    if not appid or not secret:
        cfg = Path("~/.config/wechat-mp/config.json").expanduser()
        if cfg.is_file():
            try:
                d = json.loads(cfg.read_text())
                appid = appid or d.get("appid", "")
                secret = secret or d.get("secret", "")
            except Exception:
                pass
    if not appid or not secret:
        raise WxError(
            -3,
            "缺少 WX_APPID / WX_SECRET。设置环境变量，或写入 ~/.config/wechat-mp/config.json",
            "config",
        )
    return WxClient(appid, secret)


def validate_article(article: dict) -> list[str]:
    """提交前拦截，不静默截断。标题超长在这里报，别等 40008。"""
    warns = []
    title = article.get("title") or ""
    if not title:
        warns.append("标题为空：draft/add 会失败")
    elif len(title) > TITLE_HARD:
        warns.append(f"标题 {len(title)} 字，超过微信上限 {TITLE_HARD} 字，必须改短")
    elif len(title) > TITLE_WARN:
        warns.append(f"标题 {len(title)} 字，超过 {TITLE_WARN} 字，列表页可能被截断")
    if len(article.get("digest") or "") > DIGEST_MAX:
        warns.append(f"摘要超过 {DIGEST_MAX} 字，微信会截断")
    if len(article.get("author") or "") > AUTHOR_MAX:
        warns.append(f"作者超过 {AUTHOR_MAX} 字")
    content = article.get("content") or ""
    if len(content) > CONTENT_MAX:
        warns.append(f"正文 {len(content)} 字符，超过 {CONTENT_MAX}，会被拒")
    if not article.get("thumb_media_id"):
        warns.append("缺少 thumb_media_id：草稿必须带封面")
    if "<img" in content and "mmbiz.qpic.cn" not in content and "mmbiz.qlogo.cn" not in content:
        warns.append("正文图片不是微信域名，发布后会被过滤（需先走 uploadimg 换成 URL）")
    return warns
