import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

export type WxArticle = {
  title: string;
  digest: string;
  author: string;
  content: string;
  thumb_media_id: string;
  article_type?: string;
  url?: string;
  [key: string]: unknown;
};

export class WxError extends Error {
  code: number | null;
  ambiguous: boolean;

  constructor(message: string, code: number | null = null, ambiguous = false) {
    super(message);
    this.name = "WxError";
    this.code = code;
    this.ambiguous = ambiguous;
  }
}

type RecordValue = Record<string, unknown>;

function isRecord(value: unknown): value is RecordValue {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function singleArticle(news: unknown): WxArticle | null {
  if (!Array.isArray(news) || news.length !== 1 || !isRecord(news[0])) return null;
  const item = news[0];
  if (item.article_type !== undefined && item.article_type !== "news") return null;
  for (const key of ["title", "content", "thumb_media_id"]) {
    if (typeof item[key] !== "string") throw new WxError("微信返回的文章字段不完整。");
  }
  for (const key of ["author", "digest"]) {
    if (item[key] !== undefined && typeof item[key] !== "string") throw new WxError("微信返回的文章字段无效。");
  }
  return { author: "", digest: "", ...item } as WxArticle;
}

function requiredString(reply: RecordValue, key: string, write: boolean): string {
  const value = reply[key];
  if (typeof value !== "string" || !value.trim()) {
    throw new WxError(`微信响应缺少 ${key}。`, null, write);
  }
  return value;
}

export class WechatClient {
  #appid: string;
  #secret: string;
  #accessToken = "";
  #expiresAt = 0;

  constructor(appid: string, secret: string) {
    if (!appid.trim() || !secret.trim()) throw new WxError("请配置公众号 AppID 和 AppSecret。");
    this.#appid = appid.trim();
    this.#secret = secret.trim();
  }

  #redact(value: unknown): string {
    let message = typeof value === "string" ? value : "";
    for (const credential of [this.#secret, this.#accessToken, this.#appid]) {
      if (credential) {
        message = message.replaceAll(credential, "[已隐藏]").replaceAll(encodeURIComponent(credential), "[已隐藏]");
      }
    }
    return message.replace(/((?:access_token|appsecret|secret|appid)\s*[=:]\s*)[^\s&]+/gi, "$1[已隐藏]")
      .replace(/[\r\n\t]+/g, " ").slice(0, 500);
  }

  async #request(path: string, payload: RecordValue | FormData, options: { write?: boolean; auth?: boolean; type?: string } = {}): Promise<RecordValue> {
    const write = options.write === true;
    const url = new URL(path, "https://api.weixin.qq.com/cgi-bin/");
    if (options.auth !== false) url.searchParams.set("access_token", await this.token());
    if (options.type) url.searchParams.set("type", options.type);

    let response: Response;
    let result: unknown;
    try {
      const multipart = payload instanceof FormData;
      response = await fetch(url, {
        method: "POST",
        headers: multipart ? undefined : { "Content-Type": "application/json; charset=utf-8" },
        body: multipart ? payload : JSON.stringify(payload),
        redirect: "error",
        signal: AbortSignal.timeout(30_000),
      });
      result = await response.json();
    } catch {
      // Network and decoding errors can follow a successfully applied write.
      throw new WxError(`${path} 请求中断、超时或响应无法解析。`, null, write);
    }
    if (!isRecord(result)) {
      throw new WxError(`${path} 返回异常响应（HTTP ${response.status}）。`, null, write);
    }
    const code = result.errcode;
    if (!response.ok) {
      // A gateway error or timeout may arrive after the request was applied.
      // Only a non-timeout client error carrying a WeChat rejection is definitive.
      const rejected = response.status >= 400 && response.status < 500 && response.status !== 408
        && typeof code === "number" && Number.isInteger(code) && code > 0
        && typeof result.errmsg === "string" && result.errmsg.trim().length > 0;
      if (!rejected) throw new WxError(`${path} 返回异常响应（HTTP ${response.status}）。`, null, write);
    }
    if (code !== undefined && !Number.isInteger(code)) {
      throw new WxError(`${path} 返回无效错误码。`, null, write);
    }
    if (typeof code === "number" && code !== 0) {
      throw new WxError(`${path} 微信错误 ${code} ${this.#redact(result.errmsg)}`, code, write && code === -1);
    }
    return result;
  }

  async token(): Promise<string> {
    if (this.#accessToken && Date.now() < this.#expiresAt) return this.#accessToken;
    const reply = await this.#request("stable_token", {
      grant_type: "client_credential", appid: this.#appid, secret: this.#secret, force_refresh: false,
    }, { auth: false });
    const token = requiredString(reply, "access_token", false);
    const seconds = reply.expires_in;
    if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) {
      throw new WxError("微信返回的凭据有效期无效。");
    }
    this.#accessToken = token;
    this.#expiresAt = Date.now() + Math.max(0, seconds - 60) * 1000;
    return token;
  }

  async #upload(file: string, cover: boolean, expectedSha256?: string): Promise<string> {
    const bytes = await readFile(file);
    if (expectedSha256 !== undefined && createHash("sha256").update(bytes).digest("hex") !== expectedSha256) {
      throw new WxError("上传图片与已预览版本不一致。");
    }
    const isPng = bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
    const isJpeg = bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
    if (!isPng && !isJpeg) throw new WxError("请使用已处理的 JPEG 或 PNG 图片。");
    if (bytes.length >= (cover ? 10 : 1) * 1024 * 1024) throw new WxError("图片超出对应上传接口的大小限制。");
    const form = new FormData();
    form.append("media", new Blob([new Uint8Array(bytes)], { type: isPng ? "image/png" : "image/jpeg" }), isPng ? "image.png" : "image.jpg");
    const reply = cover
      ? await this.#request("material/add_material", form, { type: "image", write: true })
      : await this.#request("media/uploadimg", form, { write: true });
    if (cover) return requiredString(reply, "media_id", true);
    const url = requiredString(reply, "url", true);
    if (!URL.canParse(url) || !["https:", "http:"].includes(new URL(url).protocol)) {
      throw new WxError("微信返回的图片 URL 无效。", null, true);
    }
    return url;
  }

  uploadBody(file: string, expectedSha256?: string): Promise<string> {
    return this.#upload(file, false, expectedSha256);
  }

  uploadCover(file: string, expectedSha256?: string): Promise<string> {
    return this.#upload(file, true, expectedSha256);
  }

  async add(article: WxArticle): Promise<string> {
    const reply = await this.#request("draft/add", { articles: [article] }, { write: true });
    return requiredString(reply, "media_id", true);
  }

  async update(id: string, article: WxArticle): Promise<void> {
    const reply = await this.#request("draft/update", { media_id: id, index: 0, articles: article }, { write: true });
    if (reply.errcode !== 0) throw new WxError("微信未确认草稿更新结果。", null, true);
  }

  async get(id: string): Promise<WxArticle> {
    const reply = await this.#request("draft/get", { media_id: id });
    const article = singleArticle(reply.news_item);
    if (!article) throw new WxError("目标草稿须为单篇普通图文。");
    return article;
  }

  // Reconciliation inspects the first WeChat page (up to 20 drafts).
  async recent(): Promise<{ id: string; article: WxArticle }[]> {
    const reply = await this.#request("draft/batchget", { offset: 0, count: 20, no_content: 0 });
    if (reply.item_count === 0 && reply.item === undefined) return [];
    if (!Array.isArray(reply.item)) throw new WxError("微信返回的草稿列表无效。");
    const items: { id: string; article: WxArticle }[] = [];
    for (const item of reply.item) {
      if (!isRecord(item) || !isRecord(item.content)) throw new WxError("微信返回的草稿列表项无效。");
      const article = singleArticle(item.content.news_item);
      if (article) items.push({ id: requiredString(item, "media_id", false), article });
    }
    return items;
  }
}
