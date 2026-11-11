import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { python } from "../skills/wechat-mp-publisher/scripts/editor.ts";
import { loadBundle, preview } from "../skills/wechat-mp-publisher/scripts/preview.ts";
import { articleHtml, scenes } from "../skills/wechat-mp-publisher/scripts/render.ts";

test("preview freezes the reviewed article, layout and photos and invalidates superseded approvals", async t => {
  const root = await mkdtemp(join(tmpdir(), "wx-preview-test-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  execFileSync(python(), ["-c", "from PIL import Image; import sys; from pathlib import Path; d=Path(sys.argv[1]); Image.new('RGB',(8,6),'red').save(d/'一.png'); Image.new('RGB',(6,8),'blue').save(d/'二.png')", root]);
  const images = ["一.png", "二.png"].map(name => join(root, name));
  const source = "“原定周六，后来没去。”\r\n\r\n晴天 & 雨天。\n<script>alert(1)</script>";
  const input = { workdir: join(root, "draft"), images, text: source, captions: ["红色", "蓝色"], author: "我" };
  const [first, same] = await Promise.all([preview(input), preview(input)]);
  assert.equal(first.version, same.version);
  const bundle = await loadBundle(first.bundleDir, { requireCurrent: true });
  assert.equal(bundle.title, "“原定周六，后来没去。”");
  assert.equal(bundle.html.includes("&lt;script&gt;alert(1)&lt;/script&gt;"), true);
  assert.equal(bundle.html.includes("晴天 &amp; 雨天。<br/>"), true);
  assert.equal(bundle.html.indexOf("红色") < bundle.html.indexOf("蓝色"), true);
  assert.deepEqual(bundle.layout, { scene: "daily", order: [1, 2], cover: 1 });

  const revised = await preview({ ...input, images: images.toReversed(), captions: input.captions.toReversed(),
    imageNumbers: [2, 1], cover: images[1], scene: "travel", suggestions: ["只在审阅区显示"] });
  assert.equal(revised.articleId, first.articleId);
  assert.notEqual(revised.version, first.version);
  const latest = await loadBundle(revised.bundleDir, { requireCurrent: true });
  assert.deepEqual(latest.layout, { scene: "travel", order: [2, 1], cover: 2 });
  assert.equal(latest.html.includes("只在审阅区显示"), false);
  assert.match(await readFile(revised.previewPath, "utf8"), /只在审阅区显示/);
  await assert.rejects(loadBundle(first.bundleDir, { requireCurrent: true }), /已有新版/);
  assert.equal((await loadBundle(first.bundleDir)).version, first.version);
  await writeFile(images[0], "用户更换了源文件");
  assert.equal((await loadBundle(revised.bundleDir)).version, revised.version);
  await writeFile(join(revised.bundleDir, latest.images[0].path), "tampered");
  await assert.rejects(loadBundle(revised.bundleDir), /预览图片已改变/);
  await writeFile(first.previewPath, "changed");
  await assert.rejects(loadBundle(first.bundleDir), /预览或正文已改变/);
});

test("user-supplied fields over WeChat limits fail without truncation", async () => {
  const input = { workdir: ".", text: "原文", images: ["unused.png"] };
  await assert.rejects(preview({ ...input, title: "🪁".repeat(33) }), /标题/);
  await assert.rejects(preview({ ...input, digest: "摘".repeat(121) }), /摘要/);
  await assert.rejects(preview({ ...input, author: "作".repeat(17) }), /作者/);
});

test("every scene dresses the same ordinary text and ordered photos without writing new story details", () => {
  const photos = [{ path: "images/body-1.jpg", caption: "" }, { path: "images/body-2.jpg", caption: "" }];
  const content = Object.keys(scenes).map(scene => articleHtml("出门，绕了一圈。\n\n回家。", photos, scene, "normal"));
  assert.equal(new Set(content).size, 4);
  for (const html of content) {
    assert.equal(html.replace(/<[^>]*>/g, ""), "出门，绕了一圈。回家。");
    assert.deepEqual(Array.from(html.matchAll(/<img src="([^"]+)"/g), match => match[1]), photos.map(p => p.path));
  }
});
