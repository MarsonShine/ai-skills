import { createHash } from 'node:crypto';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { assertCurrent, type Bundle } from './preview.ts';
import { WxError, type WechatClient, type WxArticle } from './wechat.ts';

type Action = 'draft' | 'update' | 'status';
type Options = { confirmed?: string; overwrite?: string; claim?: string };
type Intent = {
  action: 'draft' | 'update'; version: string; article: WxArticle;
  previous?: string; previousIds?: string[];
};
type RecordState = {
  assets: Record<string, string>; id?: string; baseline?: WxArticle; version?: string; intent?: Intent;
};

function hash(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export function confirmation(action: string, appid: string, bundle: Bundle): string {
  return hash([action, appid, bundle.articleId, bundle.version]);
}

// The renderer generates a constrained HTML fragment. Unknown tags and attributes
// participate in comparison, so unexpected editor transformations remain visible.
const tags = /<!--[\s\S]*?-->|<\/?[a-z][\w:-]*(?:[^<>"']|"[^"]*"|'[^']*')*>/gi;
const attributes = /([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
const voidTags = new Set(['img', 'br', 'hr', 'wbr', 'input', 'source']);
function decode(text: string): string {
  const names: Record<string, string> = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: '\u00a0' };
  return text.replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi, (original, key: string) => {
    if (key[0] !== '#') return names[key.toLowerCase()];
    const code = key[1].toLowerCase() === 'x' ? parseInt(key.slice(2), 16) : Number(key.slice(1));
    return code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : original;
  });
}

function inspectHTML(html: string) {
  const parts: unknown[] = [], images: string[] = [];
  let cursor = 0;
  function appendText(text: string) {
    if (text) parts.push(['text', decode(text.replace(/\r\n?/g, '\n'))]);
  }
  for (const match of html.matchAll(tags)) {
    appendText(html.slice(cursor, match.index));
    const tag = match[0];
    cursor = match.index + tag.length;
    if (tag.startsWith('<!--')) continue;
    const name = tag.match(/^<\/?([\w:-]+)/)![1].toLowerCase();
    if (tag.startsWith('</')) {
      if (!voidTags.has(name)) parts.push(['end', name]);
      continue;
    }
    const attrs = new Map<string, string>();
    const source = tag.slice(1 + name.length).replace(/\/?\s*>$/, '');
    for (const a of source.matchAll(attributes)) {
      const key = a[1].toLowerCase();
      let value = decode(a[2] ?? a[3] ?? a[4] ?? '');
      if (key === 'style') {
        value = value.split(';').map(v => v.trim().replace(/^([\w-]+)\s*:\s*/, '$1:')).filter(Boolean).join(';');
      }
      // HTML parsers retain the first occurrence of a duplicate attribute.
      if (!attrs.has(key)) attrs.set(key, value);
    }
    if (name === 'img') images.push(attrs.get('src') ?? '');
    parts.push(['start', name, [...attrs].sort(([a], [b]) => a.localeCompare(b, 'en'))]);
  }
  appendText(html.slice(cursor));
  return { parts, images };
}

function articleView(article: WxArticle) {
  const html = inspectHTML(article.content);
  return {
    title: article.title, author: article.author || '', digest: article.digest || '',
    article_type: article.article_type || 'news', cover: article.thumb_media_id,
    images: html.images, content: html.parts,
  };
}

// These editorial settings are writable through draft/update but are not owned
// by the local renderer. Carry them from the fresh remote read on every update.
const editorialFields = [
  'content_source_url', 'need_open_comment', 'only_fans_can_comment',
  'pic_crop_235_1', 'pic_crop_1_1', 'cover_info', 'product_info',
];
function settings(article: WxArticle) {
  return Object.fromEntries(editorialFields.filter(key => article[key] != null).map(key => [key, article[key]]));
}

function remoteHash(article: WxArticle): string {
  return hash([articleView(article), settings(article)]);
}

function redacted(text: string) {
  return text.replace(/\b(access_token|appsecret|secret|authorization|token)\s*[:=]\s*["']?[^\s"'&,}]+/gi, '$1=[已隐藏]')
    .replace(/\bBearer\s+[^\s"'&,}]+/gi, 'Bearer [已隐藏]');
}

function snippet(value: unknown): string {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  const clean = redacted(text ?? '');
  return clean.length > 220 ? clean.slice(0, 219) + '…' : clean;
}

function excerptChanges(before: unknown, after: unknown) {
  const printable = (value: unknown) => redacted(typeof value === 'string' ? value : JSON.stringify(value) ?? '');
  const oldText = printable(before), newText = printable(after);
  let i = 0;
  while (i < oldText.length && i < newText.length && oldText[i] === newText[i]) i++;
  const start = Math.max(0, i - 40);
  const extract = (text: string) => (start ? '…' : '') + snippet(text.slice(start));
  return { old: extract(oldText), current: extract(newText) };
}

function safeLink(article: WxArticle) {
  if (typeof article.url !== 'string' || !URL.canParse(article.url)) return {};
  const url = new URL(article.url);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || redacted(url.href) !== url.href) return {};
  return { preview_url: url.href };
}

function differences(expected: WxArticle, actual: WxArticle, compareSettings = false) {
  const a = articleView(expected), b = articleView(actual);
  const checks = Object.fromEntries((Object.keys(a) as (keyof typeof a)[]).map(key => [key, hash(a[key]) === hash(b[key])]));
  const changed = Object.keys(checks).filter(key => !checks[key]);
  const details: Record<string, unknown> = {};
  for (const key of changed as (keyof typeof a)[]) {
    if (key === 'content') {
      let i = 0;
      while (i < a.content.length && i < b.content.length && hash(a.content[i]) === hash(b.content[i])) i++;
      details.content = { at: i + 1, ...excerptChanges(a.content[i], b.content[i]) };
    } else if (key === 'images') {
      const positions = [];
      for (let i = 0; i < Math.max(a.images.length, b.images.length) && positions.length < 12; i++) {
        if (a.images[i] !== b.images[i]) positions.push({ position: i + 1, old: snippet(a.images[i]), current: snippet(b.images[i]) });
      }
      details.images = { old_count: a.images.length, current_count: b.images.length, positions };
    } else {
      details[key] = { old: snippet(a[key]), current: snippet(b[key]) };
    }
  }
  if (compareSettings && hash(settings(expected)) !== hash(settings(actual))) {
    changed.push('editor_settings');
    const edits = Object.fromEntries(editorialFields.filter(key => JSON.stringify(expected[key]) !== JSON.stringify(actual[key]))
      .map(key => [key, { old: snippet(expected[key]), current: snippet(actual[key]) }]));
    details.editor_settings = edits;
  }
  return { checks, changed, differences: details };
}

function failure(status: string, message: string, extra: object = {}) {
  return { ok: false, status, message, ...extra };
}

function errorDetails(error: unknown) {
  const e = error as { code?: number; message?: string; ambiguous?: boolean } | undefined;
  return { code: typeof e?.code === 'number' ? e.code : null, ambiguous: e?.ambiguous !== false,
    ...(error instanceof WxError ? { errmsg: snippet(error.message) } : {}) };
}

async function prepare(bundleDir: string, bundle: Bundle, state: RecordState, save: () => void, client: WechatClient): Promise<WxArticle> {
  const byPath = new Map(bundle.images.map(image => [image.path, image]));
  async function upload(path: string, role: 'body' | 'cover') {
    const image = byPath.get(path);
    if (!image) throw new Error('图片缺少预览清单记录，请重新预览。');
    const key = role + ':' + image.sha256;
    if (!state.assets[key]) {
      const file = join(bundleDir, path);
      await assertCurrent(bundleDir, bundle);
      state.assets[key] = role === 'body' ? await client.uploadBody(file, image.sha256) : await client.uploadCover(file, image.sha256);
      save();
    }
    return state.assets[key];
  }
  const urls = new Map<string, string>();
  for (const path of new Set(inspectHTML(bundle.html).images)) urls.set(path, await upload(path, 'body'));
  const content = bundle.html.replace(tags, tag => {
    if (!/^<img\b/i.test(tag)) return tag;
    // Only edit the generated src attribute. A caption or alt may itself
    // contain text that looks like an image path or an attribute.
    return tag.replace(attributes, (attr, name: string, double: string, single: string, bare: string) => {
      if (name.toLowerCase() !== 'src') return attr;
      const url = urls.get(decode(double ?? single ?? bare));
      if (!url) throw new Error('图片地址与预览清单不符。');
      return 'src="' + url.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;') + '"';
    });
  });
  if ([...content].length >= 20000 || Buffer.byteLength(content) >= 1024 * 1024) {
    throw new Error('微信图片地址替换后正文超限，请缩短文章或简化样式后重新预览。');
  }
  return {
    article_type: 'news', title: bundle.title, author: bundle.author, digest: bundle.digest,
    content, thumb_media_id: await upload(bundle.cover, 'cover'),
  };
}

async function synchronize(action: Action, bundleDir: string, bundle: Bundle, appid: string, state: RecordState,
    save: () => void, client: WechatClient, options: Options): Promise<object> {
  const authorized = options.confirmed === confirmation(action, appid, bundle);
  const needsConfirmation = () => failure('confirmation_required', '请确认本次操作、目标账号和预览版本。');

  function conflict(remote: WxArticle) {
    const overwrite = hash(['overwrite', confirmation('update', appid, bundle), state.id, remoteHash(remote)]);
    const base = state.baseline ?? state.intent?.article;
    const difference = base ? differences(base, remote, true) : {};
    return { overwrite, result: failure('conflict', '后台草稿与上次记录不同，请核对后决定是否覆盖。', {
      media_id: state.id, ...difference, remote_title: remote.title, local_title: bundle.title, overwrite, ...safeLink(remote),
    }) };
  }
  function verified(remote: WxArticle, expected: WxArticle, version: string, reused: boolean) {
    const diff = differences(expected, remote);
    if (diff.changed.length) return failure('verification_mismatch', '草稿已写入，回读与预览不同。', {
      media_id: state.id, ...diff, version, ...safeLink(remote),
    });
    state.baseline = remote;
    state.version = version;
    delete state.intent;
    save();
    return { ok: true, status: 'verified', media_id: state.id, version, matches_preview: version === bundle.version,
      reused, checks: diff.checks, ...safeLink(remote) };
  }
  async function readKnown() {
    try { return { remote: await client.get(state.id!) }; }
    catch (error) {
      const problem = errorDetails(error);
      if (problem.code === 40007) return { result: failure('missing', '微信未找到此草稿，可能已发表或删除。', { media_id: state.id, ...problem }) };
      return { result: failure(state.intent ? 'awaiting_verification' : 'read_failed',
        state.intent ? '草稿编号已保存，回读待核验。请重试 status。' : '暂时无法读取草稿，请重试 status。',
        { media_id: state.id, ...problem }) };
    }
  }

  // An add may have succeeded before the process received (or persisted)
  // media_id. Without identity evidence a retry must never create another.
  if (state.intent && !state.id) {
    const intent = state.intent;
    let candidates: { id: string; article: WxArticle }[];
    try {
      candidates = options.claim ? [{ id: options.claim, article: await client.get(options.claim) }] : await client.recent();
    } catch (error) {
      return failure('creation_unknown', '创建结果待核对，未能读取微信草稿。', errorDetails(error));
    }
    candidates = candidates.filter(c => !intent.previousIds?.includes(c.id) && !differences(intent.article, c.article).changed.length);
    if (candidates.length !== 1 || (!intent.previousIds && !options.claim)) return failure('creation_unknown', '请在微信后台核对草稿，找到后用候选 media_id 认领。', {
      candidates: candidates.map(c => c.id),
      candidate_details: candidates.map(({ id, article }) => ({
        media_id: id, title: article.title, author: article.author, digest: snippet(article.digest),
        cover: snippet(article.thumb_media_id), image_count: inspectHTML(article.content).images.length, ...safeLink(article),
      })),
    });
    state.id = candidates[0].id;
    save();
  }

  let remote: WxArticle | undefined;
  if (state.id) {
    const read = await readKnown();
    if (!read.remote) return read.result!;
    remote = read.remote;
    if (state.intent) {
      const intent = state.intent;
      if (!differences(intent.article, remote).changed.length) {
        const completed = verified(remote, intent.article, intent.version, true);
        if (action === 'status' || intent.version === bundle.version) return completed;
      } else {
        const retryUpdate = intent.action === 'update' && intent.previous === remoteHash(remote);
        const overwrite = conflict(remote);
        if (action !== 'update' || (!retryUpdate && options.overwrite !== overwrite.overwrite)) {
          const diff = differences(intent.article, remote);
          return failure('verification_mismatch', '草稿编号已保存，回读与上次提交内容不同，请核对后处理。', {
            media_id: state.id, ...diff, ...safeLink(remote), overwrite: overwrite.overwrite,
          });
        }
      }
    }
    if (state.baseline && remoteHash(state.baseline) !== remoteHash(remote)) {
      const mismatch = conflict(remote);
      if (action !== 'update' || options.overwrite !== mismatch.overwrite) return mismatch.result;
    } else if (!state.intent && (action === 'status' || state.version === bundle.version)) {
      return verified(remote, state.baseline!, state.version!, true);
    }
    if (action === 'draft') return failure('update_required', '此文章已有关联草稿，请使用 update 更新。', { media_id: state.id });
  } else if (action !== 'draft') {
    return failure('no_draft', '此文章尚未关联草稿。');
  }

  if (action === 'status') return failure('awaiting_verification', '草稿等待核验。', { media_id: state.id });
  if (!authorized) return needsConfirmation();
  let previousIds: string[] | undefined;
  if (action === 'draft') {
    try { previousIds = (await client.recent()).map(item => item.id); }
    catch { /* The list is optional evidence for recovery, not a prerequisite for creating a draft. */ }
  }
  const article = { ...(remote ? settings(remote) : {}), ...await prepare(bundleDir, bundle, state, save, client) };
  const intent: Intent = { action, version: bundle.version, article };
  if (remote) {
    // Uploading can take time, during which the owner may edit in WeChat.
    const latest = await readKnown();
    if (!latest.remote) return latest.result!;
    if (remoteHash(remote) !== remoteHash(latest.remote)) return conflict(latest.remote).result;
    intent.previous = remoteHash(remote);
  }
  // Exclude identical drafts which already existed. A recent list is bounded;
  // a sentinel-free match is corroborated by the exact uploaded image/cover IDs.
  else intent.previousIds = previousIds;
  await assertCurrent(bundleDir, bundle);
  const priorIntent = state.intent;
  state.intent = intent;
  save();
  try {
    if (action === 'draft') state.id = await client.add(article);
    else await client.update(state.id!, article);
  } catch (error) {
    const problem = errorDetails(error);
    if (!problem.ambiguous) {
      state.intent = priorIntent;
      if (problem.code === 40007) delete state.assets['cover:' + bundle.images.find(i => i.path === bundle.cover)?.sha256];
      save();
      return failure('rejected', '微信未接受本次草稿写入。', { ...problem, media_id: state.id });
    }
    return failure(action === 'draft' ? 'creation_unknown' : 'awaiting_verification',
      '微信写入结果待核对。请运行 status，勿另建草稿。', { media_id: state.id, ...problem });
  }
  save();
  const read = await readKnown();
  return read.remote ? verified(read.remote, article, bundle.version, false) : read.result!;
}

export async function syncDraft(action: Action, bundleDir: string, bundle: Bundle, appid: string, stateDir: string,
    client: WechatClient, options: Options = {}): Promise<object> {
  mkdirSync(stateDir, { recursive: true, mode: 0o700 });
  // A second SQLite connection/file supplies a crash-released OS lock while
  // progress in the ledger can be committed durably before/after network I/O.
  const mutex = new DatabaseSync(join(stateDir, 'writer-lock.sqlite'));
  try {
    try { mutex.exec('BEGIN IMMEDIATE'); }
    catch (e) {
      if ((e as { errcode?: number }).errcode === 5) return failure('busy', '另一项草稿操作正在进行，请稍后重试。');
      throw e;
    }
    const ledger = new DatabaseSync(join(stateDir, 'ledger.sqlite'));
    try {
      ledger.exec('PRAGMA synchronous=FULL; CREATE TABLE IF NOT EXISTS drafts (key TEXT PRIMARY KEY, state TEXT NOT NULL)');
      const key = hash([appid, bundle.articleId]);
      const row = ledger.prepare('SELECT state FROM drafts WHERE key=?').get(key);
      const state: RecordState = row ? JSON.parse(String(row.state)) : { assets: {} };
      const write = ledger.prepare('INSERT OR REPLACE INTO drafts(key,state) VALUES(?,?)');
      const save = () => { write.run(key, JSON.stringify(state)); };
      return await synchronize(action, bundleDir, bundle, appid, state, save, client, options);
    } finally { ledger.close(); }
  } finally { mutex.close(); }
}
