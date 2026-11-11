import { execFile } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { link, mkdir, mkdtemp, readFile, realpath, rename, rm, writeFile } from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { python as defaultPython } from "./editor.ts";
import { articleHtml, reviewHtml, scenes, type Scene } from "./render.ts";

type Change = { before: string; after: string; reason: string };
type Quality = "balanced" | "lossless";
export type PreviewInput = {
  text: string; images: string[]; workdir: string; title?: string; digest?: string; author?: string;
  cover?: string; scene?: string; captions?: string[]; epigraph?: string; quality?: Quality; python?: string;
  footerImage?: string; footerText?: string;
  profile?: { author?: string; scene?: string; whitespace?: string };
  imageNumbers?: number[]; coverNumber?: number; changes?: Change[]; suggestions?: string[];
};
export type EditorLayout = { scene: Scene; order: number[]; cover?: number };
type Image = { path: string; sha256: string };
export type BundleContent = {
  schema: 1; articleId: string; title: string; digest: string; author: string;
  html: string; cover: string; images: Image[]; layout: EditorLayout; changes: Change[]; suggestions: string[];
};
export type Bundle = BundleContent & { version: string; previewSha256: string };

const run = promisify(execFile);
const helper = fileURLToPath(new URL("./images.py", import.meta.url));
const sha256 = (bytes: Buffer | string) => createHash("sha256").update(bytes).digest("hex");
const code = (error: unknown) => (error as NodeJS.ErrnoException).code;

async function articleIdentity(workdir: string, stage: string): Promise<string> {
  // Two simultaneous first previews must get the same identity, even if the process stops midway.
  const candidate = join(stage, ".id");
  const target = join(workdir, ".article-id");
  await writeFile(candidate, randomUUID());
  try {
    await link(candidate, target);
  } catch (error) {
    if (code(error) !== "EEXIST") throw error;
  }
  await rm(candidate);
  const identity = await readFile(target, "utf8");
  if (!/^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$/i.test(identity)) throw new Error("文章目录内的标识无效。");
  return identity;
}

async function prepareImage(source: string, folder: string, stem: string, quality: Quality, python: string) {
  const args = ["-X", "utf8", "-B", helper, "--input", resolve(source), "--out-dir", folder, "--stem", stem,
    "--role", stem === "cover" ? "cover" : "body", "--quality", quality];
  let stdout: string;
  try {
    ({ stdout } = await run(python, args, { encoding: "utf8", windowsHide: true }));
  } catch (error) {
    const failure = error as { stdout?: string; stderr?: string; message: string };
    let result;
    try { result = JSON.parse(failure.stdout || ""); } catch { /* The interpreter itself may be missing. */ }
    const reason = result?.error || failure.stderr?.trim() || failure.message;
    throw Object.assign(new Error(`${basename(source)}（${stem === "cover" ? "封面" : "正文图"}）：${reason}`), { exitCode: result?.code || 2 });
  }
  const result = JSON.parse(stdout);
  if (result.ok !== true || typeof result.path !== "string") throw new Error("图片处理未返回有效文件。");
  const name = basename(result.path);
  if (dirname(resolve(result.path)) !== folder || !new RegExp(`^${stem}\\.(jpg|jpeg|png)$`, "i").test(name)) {
    throw new Error("图片处理返回的文件名与当前文章不匹配。");
  }
  const image = { path: "images/" + name, sha256: sha256(await readFile(result.path)) };
  const { path: _path, ...measurement } = result;
  return { image, measurement };
}

function limit(value: string, maximum: number, label: string): string {
  if (typeof value !== "string" || Array.from(value).length > maximum) throw new Error(`${label}须为不超过 ${maximum} 个字的文字。`);
  return value;
}

function excerpt(source: string, length: number): string {
  return Array.from(source).slice(0, length).join("").trimEnd();
}

function validateHtml(html: string) {
  if (Array.from(html).length >= 20_000 || Buffer.byteLength(html, "utf8") >= 1024 * 1024) {
    throw new Error("微信要求正文 HTML 少于 2 万字符且小于 1 MiB，请缩短文章或减少图片与装饰。");
  }
}

function sceneFromText(text: string): Scene {
  if (/周年|纪念日|结婚纪念|生日快乐/u.test(text)) return "anniversary";
  if (/旅[行途游]|游记|出游|自驾游|行程/u.test(text)) return "travel";
  if (/亲子|孩子|女儿|儿子|宝宝|幼儿园|一家人/u.test(text)) return "family";
  return "daily";
}

function metadata(input: PreviewInput) {
  if (typeof input.text !== "string" || !input.text.trim()) throw new Error("请提供文章原文。");
  if (!Array.isArray(input.images) || !input.images.length || input.images.some(p => typeof p !== "string" || !p.trim())) {
    throw new Error("请提供至少一张正文图片。");
  }
  if (input.footerText && !input.footerImage) throw new Error("页尾文字需要配合页尾图片使用。");
  const opening = input.text.trim().split(/\r\n|[\r\n]/u)[0].trim();
  const firstSentence = opening.match(/^[^。！？!?]+(?:[。！？!?][”」』]?|$)/u)?.[0] || opening;
  const title = limit(input.title ?? excerpt(firstSentence, 32), 32, "标题");
  if (!title.trim()) throw new Error("标题不能为空。");
  const digest = limit(input.digest ?? excerpt(input.text.trim().replace(/\s+/gu, " "), 54), 120, "摘要");
  const author = limit(input.author ?? input.profile?.author ?? "", 16, "作者");
  const requested = input.scene ?? input.profile?.scene ?? "daily";
  const scene = requested === "auto" ? sceneFromText(input.text) : requested;
  if (!Object.hasOwn(scenes, scene)) throw new Error("请从 daily、family、travel、anniversary 中选择场景。");
  const whitespace = input.profile?.whitespace ?? "normal";
  if (!["tight", "normal", "airy"].includes(whitespace)) throw new Error("留白须为 tight、normal 或 airy。");
  const order = input.imageNumbers ?? input.images.map((_, i) => i + 1);
  if (order.length !== input.images.length || new Set(order).size !== order.length ||
      order.some(n => !Number.isInteger(n) || n < 1 || n > order.length)) throw new Error("图序应包含所有原图的编号，各一次。");
  const coverIndex = input.cover ? input.images.findIndex(p => resolve(p) === resolve(input.cover!)) : 0;
  const cover = input.coverNumber ?? (coverIndex < 0 ? undefined : order[coverIndex]);
  if (cover !== undefined && !order.includes(cover)) throw new Error("封面编号须对应一张原图。");
  const layout: EditorLayout = { scene: scene as Scene, order, ...(cover === undefined ? {} : { cover }) };
  if (input.captions && (input.captions.length > order.length || input.captions.some(c => typeof c !== "string"))) {
    throw new Error("请按原图顺序提供文字图注。");
  }
  return { title, digest, author, layout, whitespace };
}

export async function assertCurrent(bundleDir: string, bundle: Pick<Bundle, "articleId" | "version">) {
  const workdir = dirname(dirname(resolve(bundleDir)));
  const current = JSON.parse(await readFile(join(workdir, "current.json"), "utf8"));
  if (current.articleId !== bundle.articleId || current.version !== bundle.version) {
    throw new Error("这份预览已有新版，请重新打开并确认当前版本。");
  }
}

export async function loadBundle(bundleDir: string, options: { requireCurrent?: boolean } = {}): Promise<Bundle> {
  const root = await realpath(resolve(bundleDir));
  const bundle = JSON.parse(await readFile(join(root, "bundle.json"), "utf8")) as Bundle;
  const { version, ...manifest } = bundle;
  if (manifest.schema !== 1 || version !== basename(root) || sha256(JSON.stringify(manifest)) !== version) {
    throw new Error("文章包的版本或清单已改变，请重新生成预览。");
  }
  if (await readFile(join(root, "content.html"), "utf8") !== bundle.html ||
      sha256(await readFile(join(root, "preview.html"))) !== bundle.previewSha256) {
    throw new Error("预览或正文已改变，请重新生成预览。");
  }
  if (!bundle.images.some(i => i.path === bundle.cover)) throw new Error("预览缺少封面。");
  for (const image of bundle.images) {
    if (!/^images\/(?:body-\d+|cover)\.(?:png|jpe?g)$/i.test(image.path)) throw new Error("文章包的图片路径无效。");
    const file = resolve(root, image.path);
    if (await realpath(file) !== file || sha256(await readFile(file)) !== image.sha256) {
      throw new Error(`预览图片已改变：${image.path}。请重新生成预览。`);
    }
  }
  if (options.requireCurrent) await assertCurrent(root, bundle);
  return bundle;
}

export async function preview(input: PreviewInput) {
  const { title, digest, author, layout, whitespace } = metadata(input);
  const quality = input.quality ?? "balanced";
  if (quality !== "balanced" && quality !== "lossless") throw new Error("画质须为 balanced 或 lossless。");
  const python = input.python ?? defaultPython();
  const workdir = resolve(input.workdir);
  const versions = join(workdir, "versions");
  await mkdir(versions, { recursive: true });
  const stage = await mkdtemp(join(workdir, ".preview-"));
  const pointer = join(workdir, ".current-" + randomUUID());
  try {
    const articleId = await articleIdentity(workdir, stage);
    const imageDir = join(stage, "images");
    await mkdir(imageDir);
    const prepared = [];
    for (const [i, file] of input.images.entries()) {
      prepared.push(await prepareImage(file, imageDir, `body-${i + 1}`, quality, python));
    }
    const footer = input.footerImage
      ? await prepareImage(input.footerImage, imageDir, `body-${input.images.length + 1}`, "lossless", python)
      : undefined;
    const cover = await prepareImage(input.cover ?? input.images[0], imageDir, "cover", quality, python);
    const photos = prepared.map(({ image }, i) => ({ path: image.path, caption: input.captions?.[i] || "" }));
    const html = articleHtml(input.text, photos, layout.scene, whitespace, input.epigraph,
      footer && { path: footer.image.path, text: input.footerText ?? "" });
    validateHtml(html);
    const images = [...prepared.map(p => p.image), ...(footer ? [footer.image] : []), cover.image];
    const content: BundleContent = { schema: 1, articleId, title, digest, author, html, cover: cover.image.path,
      images, layout, changes: input.changes ?? [], suggestions: input.suggestions ?? [] };
    const page = reviewHtml(content);
    const manifest = { ...content, previewSha256: sha256(page) };
    const version = sha256(JSON.stringify(manifest));
    const result = { ...manifest, version };
    await writeFile(join(stage, "content.html"), html);
    await writeFile(join(stage, "preview.html"), page);
    await writeFile(join(stage, "bundle.json"), JSON.stringify(result, null, 2));
    const bundleDir = join(versions, version);
    try {
      await rename(stage, bundleDir);
    } catch (error) {
      if (!["EEXIST", "ENOTEMPTY", "EPERM", "EACCES"].includes(code(error) ?? "")) throw error;
      // An identical immutable revision may have been created by a parallel preview.
      await loadBundle(bundleDir);
    }
    await writeFile(pointer, JSON.stringify({ articleId, version }));
    await rename(pointer, join(workdir, "current.json"));
    return { ok: true, articleId, version, bundleDir, previewPath: join(bundleDir, "preview.html"), title, digest,
      scene: layout.scene, quality: [...prepared, ...(footer ? [footer] : []), cover].map(p => p.measurement) };
  } finally {
    await rm(pointer, { force: true });
    await rm(stage, { recursive: true, force: true });
  }
}
