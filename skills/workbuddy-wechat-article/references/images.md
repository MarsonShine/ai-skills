# 图片质量

微信会在入库时重新编码。所谓“无损上传”只有一种情况成立：输入落在它不做有损处理的区间，并且上传后回读像素仍然一致。截图、图表、设计稿、带文字的图用 PNG 有机会真无损；摄影照片做不到。

## 两个上限

| 用途 | 接口 | 单图上限 |
| --- | --- | --- |
| 正文图 | `media/uploadimg` | 1 MiB |
| 封面 | `material/add_material` | 10 MiB |

`3000×2000` 的照片转 PNG 常有 8–15 MB，正文图根本传不上去。封面走 10 MiB 上限，比正文容易做到无损。

## 四档

| 档 | 顺序与行为 | 适用 |
| --- | --- | --- |
| `lossless` | 不缩尺寸、不降质量。PNG 原像素输出；JPEG 保持 JPEG 并明确标记有损；超限直接 `exit 7` | 截图、图表、设计稿、带字图 |
| `high` | 只在超尺寸时缩；JPEG 质量锁 92；PNG 优先保留 | 需要画质、又能接受少量尺寸调整 |
| `balanced`（默认） | 先定尺寸，再定格式，最后从 95 往下二分找可用最高质量 | 大多数正文图 |
| `small` | 宽度压到 1080，JPEG 质量 80，必要时继续缩 | 图多、省流量 |

顺序不能反：先定尺寸 → 再定格式 → 最后才谈质量。顺序错了，细节在第一步就丢了。

## 什么叫无损

本地：

- `lossless` 档的 PNG 必须与解码后的源像素逐点相同（`pixel_equal: true`），尺寸不变，才写 `lossless: true`。
- 16 位 PNG、CMYK 等无法在不改像素的前提下输出，`lossless` 档直接报错。
- JPEG 源图本身已经有损。`lossless` 档不缩、不降质量，但仍会标记 `lossless: false`，理由写明“JPEG 源图本身有损”。

远端：

- `draft` 会把每张上传后的 CDN 图下载回来，用 Pillow 比较尺寸、字节和像素。
- 只有 `quality == lossless` 且远端 `pixel_equal` 才写 `lossless: true`。
- 尺寸被缩、质量被压、微信转码，都会写 `lossless: false` 并给出原因。

不要用 pngquant 冒充“无损量化”：pngquant 是有损调色板量化。严格无损档不做调色板量化。

## 超限时

`--quality lossless` 遇到无法在不变像素前提下处理的情况，返回：

```json
{
  "ok": false,
  "code": 7,
  "error": "无损 PNG 为 2434352 字节，超过 body 上限 1048576 字节……",
  "options": [
    {"action": "resize", "size": "561x561", "note": "缩尺寸后仍是 PNG，但像素已变化"},
    {"action": "format", "format": "jpeg", "note": "换 JPG 可显著减小体积，但有损"},
    {"action": "quality", "quality": "balanced", "note": "自动找最高可用质量并报告降了什么"}
  ]
}
```

把选择交给作者，不要自动缩。作者明确同意后才换档，并在报告里写清降了什么。

## 预演

```text
python -X utf8 scripts/article.py qc --blocks 文章.json --quality lossless --out-dir 临时目录
```

`qc` 不上传、不渲染，只跑预处理并输出每张图的 `src_px`、`output_px`、`src_bytes`、`output_bytes`、`format`、`pixel_equal`、`lossless`、`reason`。适合在写稿前先知道哪张图过不了 1 MiB。

## 尺寸阈值

社区里“宽度必须 1080”和“1280”两个值并存（1080 更像后台编辑器路径）。本技能默认 `--max-width 1280`，但不把它当真理：最终以 `draft` 回读的 `cdn_px` 为准。微信以后改规则，回读结果会立刻暴露，不用等读者说糊。

## 高图

PNG 高度超过 29999px、JPEG 超过 16383px 会被微信拒绝或缩放。`qc`/`preview` 会在上传前报错，不把失败留到草稿阶段。
