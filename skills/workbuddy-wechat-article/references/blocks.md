# 块与场景

文章是一个 JSON 文档。`blocks` 只描述“这是什么”，颜色、字号、圆角全部来自 `scripts/themes.py`。

```json
{
  "title": "豆豆的蚂蚁",
  "author": "阿柯",
  "digest": "她在门口蹲了十分钟",
  "scene": "family",
  "cover": "photos/cover.jpg",
  "blocks": [
    {"type": "lead", "text": "豆豆在门口蹲了十分钟。"},
    {"type": "p", "text": "我问她看什么，她说蚂蚁在搬饼干屑。"},
    {"type": "photo_polaroid", "src": "photos/01.jpg", "caption": "门口的水泥地"}
  ]
}
```

`title` ≤64 字，`digest` ≤120 字，`author` ≤16 字；省略时预览会从正文摘，但草稿前请让作者确认。

## 通用块

| `type` | 字段 | 用途 |
| --- | --- | --- |
| `lead` | `text` | 开场，左侧竖线强调 |
| `p` | `text` | 普通段落，支持换行 |
| `h2` / `h3` | `text` | 小标题 |
| `quote` | `text`、`source` | 引语，来源可省略 |
| `list` | `items[]` | 无序列表 |
| `callout` | `title`、`items[]` | 提示卡 |
| `image` | `src`、`caption` | 正文图 |
| `divider` | 无 | 分隔线 |
| `code` | `text` | 仅技术号使用；生活号请在 `forbid_blocks` 里禁掉 |
| `footer` | `text` | 文末说明 |

## 家庭亲子 `family`

| 块 | 字段 | 骨架 |
| --- | --- | --- |
| `photo_polaroid` | `src`、`caption` | 居中白底拍立得，1px 边框兜底阴影 |
| `kid_quote` | `text`、`nickname`、`age` | 软色卡片，真实 `“` 字符放大，底部昵称+年龄 chip |
| `checklist` | `items[]` | 每条前置 15px 方框 + `✓` |
| `dialogue` | `lines[{who,text}]` | 左右 inline-block 气泡；`who` 为 `right`/`me` 时靠右 |

## 旅行出门 `travel`

| 块 | 字段 | 骨架 |
| --- | --- | --- |
| `timeline` | `items[{time,title}]` | 左边框做时间线，`•` 标点 |
| `route_table` | `rows[{time,route}]` | 原生 table，行底细线 |
| `weather_card` | `date`、`city`、`temp`、`weather` | 纯色卡 + 大号温度 |
| `stamp` | `city`、`date` | 虚线圆形印章，正放不旋转 |

## 日常随笔 `daily`

| 块 | 字段 | 骨架 |
| --- | --- | --- |
| `drop_cap` | `text` | 首字放大，`text-indent:0` |
| `margin_note` | `note` | 便签纸 + 顶部“胶带”色块 |
| `letter_paper` | `text` | 衬线 + 左侧竖线 + 首行缩进 |
| `sign_off` | `signature`、`date` | 右对齐落款 + 细分隔线 |

## 纪念日 `anniversary`

| 块 | 字段 | 骨架 |
| --- | --- | --- |
| `countdown_card` | `number`、`unit`、`label` | 居中大号衬线数字 |
| `ticket_stub` | `title`、`date`、`city`、`years` | 左右分栏票根，虚线分隔 |
| `compare_pair` | `a`、`b`、`cap_a`、`cap_b` | `font-size:0` + 48% 双列 |
| `memory_band` | `year`、`text` | 年份定宽，正文悬挂缩进 |

## 微信不支持的写法与降级

| 想用 | 微信实际 | 本渲染器 |
| --- | --- | --- |
| flex / grid | 不支持 | inline-block + `font-size:0` + 百分比 |
| absolute / fixed | 不支持 | 普通文档流、`margin` |
| `::before` / `::after` | 被剥离 | 真实 `<span>` 放字符 |
| `transform: rotate` | 不稳 | 不旋转 |
| 渐变 | 不稳 | 纯色 + 1px 边框 |
| `calc()` | 部分剥离 | 定宽 + 负 `text-indent` |
| `box-shadow` | 部分剥离 | 同时给 `border` |

渲染器会拒绝输出含 `display:flex`、`position:absolute`、`transform`、渐变或 `calc()` 的 HTML。

## 主题无关性

同一个块在非专属场景不会丢内容：`timeline` 在家庭场景退化为“时间 + 标题”的列表，`compare_pair` 退化为两张带图注的图，`drop_cap` 退化为普通段落。`render.json` 的 `warnings` 会逐条说明哪些块用了通用骨架。

验收方式：同一份 blocks 在四套场景各渲染一次，剥掉标签后的文本必须包含所有原文与图注。
