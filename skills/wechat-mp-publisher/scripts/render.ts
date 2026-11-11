import type { BundleContent, EditorLayout } from "./preview.ts";

export const scenes = {
  daily: { label: "日常随笔", ink: "#375c4a", paper: "#f4f6ef", line: "#c3d0be", serif: true },
  family: { label: "家庭亲子", ink: "#855337", paper: "#fff7e9", line: "#e4cdb5", serif: false },
  travel: { label: "旅行出门", ink: "#365c71", paper: "#eff5f7", line: "#bfd1d8", serif: false },
  anniversary: { label: "纪念日时刻", ink: "#803f4b", paper: "#faf1ef", line: "#dfc3bb", serif: true },
};
export type Scene = keyof typeof scenes;

export function escapeHtml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function lineBreaks(value: string): string {
  return escapeHtml(value).replace(/\r\n|\n|\r/g, "<br/>");
}

type Photo = { path: string; caption: string };

export function articleHtml(text: string, photos: Photo[], scene: Scene, whitespace: string, epigraph?: string,
  footer?: { path: string; text: string }): string {
  const { ink, paper, line, serif } = scenes[scene];
  const gap = (whitespace === "airy" ? 30 : whitespace === "tight" ? 14 : 22) + (scene === "daily" ? 4 : 0);
  const font = serif ? "Georgia, 'Songti SC', SimSun, serif" : "-apple-system, 'Microsoft YaHei', sans-serif";
  const content: string[] = [];
  const quoteStyle = scene === "anniversary"
    ? `margin:0 0 ${gap}px;padding:12px 15px;border-top:1px solid ${line};border-bottom:1px solid ${line};text-align:center;font-size:19px;background:${paper};color:${ink};`
    : `margin:0 0 ${gap}px;padding:10px 16px;border-left:3px solid ${line};background:${paper};color:${ink};`;
  if (epigraph) content.push(`<section style="${quoteStyle}">${lineBreaks(epigraph)}</section>`);

  const paragraphs = text.replace(/\r\n|\r/g, "\n").split(/\n[\t ]*\n(?:[\t ]*\n)*/);
  let photoIndex = 0;
  for (const [index, paragraph] of paragraphs.entries()) {
    // Only give a quotation its own styling when the author supplied the quotation marks.
    const quoted = /^[“「『][\s\S]+[”」』]$/u.test(paragraph.trim());
    const opening = index === 0 && scene === "anniversary" && paragraph.length < 96
      ? `text-align:center;font-size:18px;color:${ink};` : "";
    const style = quoted ? quoteStyle : `margin:0 0 ${gap}px;white-space:pre-wrap;${opening}`;
    content.push(`<p style="${style}">${lineBreaks(paragraph)}</p>`);
    const photoCount = Math.round((index + 1) * photos.length / paragraphs.length);
    while (photoIndex < photoCount) {
      const photo = photos[photoIndex++];
      let frame = "";
      let marker = "";
      if (scene === "family") frame = `padding:7px 7px 12px;border:1px solid ${line};background:${paper};`;
      if (scene === "travel") {
        frame = `padding:0 0 3px 12px;border-left:2px solid ${line};`;
        marker = `<section style="font-size:0;margin:0 0 6px;"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${ink};"></span></section>`;
      }
      if (scene === "anniversary") {
        frame = photoIndex === 1 ? `padding:8px 0;border-top:1px solid ${line};border-bottom:1px solid ${line};` : "width:88%;margin-left:auto;margin-right:auto;";
      }
      const caption = photo.caption
        ? `<p style="margin:7px 0 0;text-align:center;font-size:13px;color:${ink};">${lineBreaks(photo.caption)}</p>` : "";
      content.push(`<section style="margin:0 0 ${gap}px;${frame}">${marker}<img src="${photo.path}" alt="${escapeHtml(photo.caption)}" style="display:block;width:100%;max-width:100%;height:auto;" />${caption}</section>`);
    }
  }
  if (footer) {
    const footerText = footer.text ? `<p style="margin:10px 0 0;text-align:center;font-size:13px;line-height:1.6;">${lineBreaks(footer.text)}</p>` : "";
    content.push(`<section style="margin:${gap}px 0 0;text-align:center;"><img src="${footer.path}" alt="公众号二维码" style="display:block;width:100%;max-width:198px;height:auto;margin:0 auto;" />${footerText}</section>`);
  }
  return `<section style="font-family:${font};font-size:16px;line-height:1.85;color:#292d29;overflow-wrap:break-word;">${content.join("")}</section>`;
}

// The review controls only export instructions for a new revision. Never edit the reviewed article in place.
const editorScript = `
const tools = document.querySelector("#editor");
const list = document.querySelector("#order");
const status = document.querySelector("#status");
function layout() {
  const order = Array.from(list.children, item => Number(item.dataset.id));
  const result = {scene: document.querySelector("#scene").value, order};
  const cover = document.querySelector("#cover").value;
  if (cover) result.cover = Number(cover);
  return JSON.stringify(result, null, 2);
}
function refresh() {
  Array.from(list.children).forEach((item, index) => {
    item.querySelector('[data-move="-1"]').disabled = index === 0;
    item.querySelector('[data-move="1"]').disabled = index === list.children.length - 1;
  });
  document.querySelector("#layout").value = layout();
}
tools.addEventListener("change", refresh);
tools.addEventListener("click", event => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.move) {
    const item = button.closest("li");
    const up = button.dataset.move === "-1";
    if (up && item.previousElementSibling) list.insertBefore(item, item.previousElementSibling);
    if (!up && item.nextElementSibling) list.insertBefore(item.nextElementSibling, item);
    refresh();
    item.querySelector(up ? '[data-move="1"]' : '[data-move="-1"]').focus();
  } else if (button.id === "download") {
    const url = URL.createObjectURL(new Blob([layout()], {type: "application/json"}));
    const link = document.createElement("a");
    link.href = url;
    link.download = "layout.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    status.textContent = "把 layout.json 交给助手，使用原素材生成新版预览。";
  } else if (button.id === "copy") {
    const field = document.querySelector("#layout");
    field.focus();
    field.select();
    navigator.clipboard?.writeText(field.value).then(
      () => { status.textContent = "已复制。请交给助手生成新版预览。"; },
      () => { status.textContent = "排版设置已选中，可手动复制。"; }
    );
  }
});
refresh();`;

function editor(layout: EditorLayout, images: Photo[]): string {
  const options = Object.entries(scenes).map(([key, scene]) =>
    `<option value="${key}"${key === layout.scene ? " selected" : ""}>${scene.label}</option>`).join("");
  const covers = layout.order.map(n => `<option value="${n}"${n === layout.cover ? " selected" : ""}>原图 ${n}</option>`).join("");
  const ordered = layout.order.map((n, i) => `<li data-id="${n}"><img src="${images[i].path}" alt="" /><span>原图 ${n}</span><button type="button" data-move="-1" aria-label="原图 ${n} 上移">上移</button><button type="button" data-move="1" aria-label="原图 ${n} 下移">下移</button></li>`).join("");
  return `<details id="editor"><summary>调整场景、封面和图序</summary><p>这里的调整会导出为排版设置。把设置交给助手，使用原素材生成新预览后再确认。</p>
<label>场景 <select id="scene">${options}</select></label><label>封面 <select id="cover">${layout.cover ? "" : '<option value="">保留单独提供的封面</option>'}${covers}</select></label>
<ol id="order">${ordered}</ol><label for="layout">排版设置</label><textarea id="layout" readonly rows="4"></textarea>
<button type="button" id="download">下载 layout.json</button> <button type="button" id="copy">复制设置</button><p id="status" role="status"></p></details>`;
}

export function reviewHtml(bundle: BundleContent): string {
  const { ink, paper } = scenes[bundle.layout.scene];
  const bodyImages = bundle.images.slice(0, bundle.layout.order.length).map(image => ({ ...image, caption: "" }));
  const changes = bundle.changes.length ? `<details><summary>润色改动（${bundle.changes.length}）</summary><ol>${bundle.changes.map(change => `<li><del>${lineBreaks(change.before)}</del><br/><ins>${lineBreaks(change.after)}</ins><p>${escapeHtml(change.reason)}</p></li>`).join("")}</ol></details>` : "";
  const suggestions = bundle.suggestions.length ? `<details><summary>写作提示</summary><ul>${bundle.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul></details>` : "";
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>${escapeHtml(bundle.title)} · 公众号草稿预览</title><style>
*{box-sizing:border-box}body{margin:0 auto;padding:16px;max-width:670px;background:#f0f1ee;color:#292d29;font:16px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}
main,.review{margin:18px auto;padding:20px;background:white;border-radius:8px}main{max-width:430px}#narrow:checked~main{max-width:375px}
h1,h2,p{margin-top:0}h1{font-size:25px;line-height:1.4}h2{font-size:17px}summary,button,select,input,label[for]{cursor:pointer}
button,select,textarea{font:inherit}button,select{padding:3px 8px}textarea{width:100%;font:14px/1.4 monospace}
details{margin-top:16px}details>ol,details>ul{padding-inline-start:22px}details label{display:inline-block;margin:4px 12px 4px 0}#order{padding:0;list-style:none}
#order li{display:flex;align-items:center;gap:8px;margin:6px 0}#order li img{width:52px;height:38px;object-fit:contain}#order li span{margin-right:auto}
.card{max-width:430px;margin:auto;padding:12px;background:${paper}}.card img{display:block;width:100%;max-height:180px;object-fit:contain}
.card strong,.card small{display:block}.card small{white-space:pre-wrap}.meta{color:${ink};font-size:14px}del,ins{white-space:pre-wrap}ins{color:#23523d}
</style></head><body><div class="review"><h2>封面与摘要</h2><div class="card"><img src="${bundle.cover}" alt="本版封面"><strong>${escapeHtml(bundle.title)}</strong><small>${escapeHtml(bundle.digest)}</small></div>
${changes}${suggestions}${editor(bundle.layout, bodyImages)}</div>
<input type="radio" name="width" id="narrow"><label for="narrow">375 像素</label> <input type="radio" name="width" id="wide" checked><label for="wide">430 像素</label>
<main><h1>${escapeHtml(bundle.title)}</h1>${bundle.author ? `<p class="meta">${escapeHtml(bundle.author)}</p>` : ""}${bundle.html}</main><script>${editorScript}</script></body></html>`;
}
