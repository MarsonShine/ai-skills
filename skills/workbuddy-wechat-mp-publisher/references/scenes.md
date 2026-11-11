# 场景主题包

四套主题 + 三套通用主题，全部只用内联样式、`section`/`table`/`inline-block`。
每套 = 一组 token（`scripts/themes.py`）+ 3–5 个专属块。

选包原则：**看内容，不看心情**。有孩子对话 → 家庭；有路线/时间 → 旅行；无事件的片段 → 日常；有「第几年/第几天」→ 纪念日。

---

## 家庭亲子 `family`

暖橙主色 `#e08a3c`，奶油纸 `#fffdfa`，圆角大，留白多。

| 块 | 用途 | 实现要点 |
|---|---|---|
| `photo_polaroid` | 拍立得照片 | 白底 `inline-block` 86% 宽 + 9/9/13px 内边距 + 1px 边框兜底（阴影被剥离时不塌） |
| `kid_quote` | 童言卡 | 引号用真实字符 `❝`，不用伪元素；昵称+年龄做小 chip |
| `checklist` | 出门清单 | 方框用 15×15px `inline-block` + 边框，勾选填色加 `✓` |
| `dialogue` | 对话气泡 | 左右用 `text-align` 控制，气泡 `max-width:80%` + `inline-block` |

**适用**：孩子日常、家庭记录、亲子时刻。
**不适用**：旅行攻略（信息密度不够）、纪念日（不够庄重）。

**降级**：拍立得白边被剥离 → 退成普通图片 + 图注；对话气泡对齐失效 → 加 `who` 前缀文字。

---

## 旅行出门 `travel`

雾蓝主色 `#35657e`，信息密度中等，左对齐、竖线、表格。

| 块 | 用途 | 实现要点 |
|---|---|---|
| `timeline` | 时间轴 | `border-left` 当竖线，圆点用负 `margin-left:-24px` 压线；**末项不画线**，否则拖尾巴 |
| `route_table` | 路线表 | 原生 `table`，第一列定宽 66px，行间 1px 底边 |
| `weather_card` | 天气卡 | `accent_soft` 底 + 大号温度（`FONT_MONO` 34px）+ 备注 |
| `stamp` | 地点印章 | `border:2px dashed` + `border-radius:50%`，**不旋转**（transform 不稳） |

**适用**：出门记录、行程、带娃远行。
**不适用**：纯情绪片段（表格会把气氛切碎）。

**降级**：时间轴被裁 → 去掉圆点，只留 `时间 · 事项` 两列；印章虚线变实线。

---

## 日常随笔 `daily`

墨绿主色 `#4f6b5d`，素纸 `#fdfcfa`，宋体，行高 2.1，大留白。

| 块 | 用途 | 实现要点 |
|---|---|---|
| `drop_cap` | 首字下沉 | 首字 34px `inline-block`，`vertical-align:-2px`，**不用 float** |
| `margin_note` | 页边便签 | 顶部 56×11px 半透明「胶带」，负 `margin-top:-22px` 压住上边缘 |
| `letter_paper` | 信纸 | 左侧 1px 竖线 + 段落首行缩进 2em |
| `sign_off` | 落款 | 右对齐 + 上方细线 |

**适用**：日记、无事件的日常、长文慢读。
**不适用**：信息密集的旅行记录（留白会显得空）。

**降级**：首字下沉失效 → 首字加粗；便签胶带被裁 → 退成带边框的卡片。

---

## 纪念日时刻 `anniversary`

酒红主色 `#8c2f39`，香槟金点缀 `#c9a46a`，衬线，多居中。

| 块 | 用途 | 实现要点 |
|---|---|---|
| `countdown_card` | 大数字 | 46px 数字 + 小字单位 + 说明，全居中 |
| `ticket_stub` | 票根 | **table 双栏**（64% / 中缝虚线 / 余下），右栏垂直居中 |
| `compare_pair` | 那年/今年 | 两个 48% `inline-block` + 图注，`font-size:0` 消间隙 |
| `memory_band` | 年份带 | `padding-left:58px` + `text-indent:-58px`，年份 `inline-block` 定宽 |

**适用**：纪念日、生日、周年、回顾。
**不适用**：日常流水（太重）。

**降级**：票根圆角失效（table 上 `border-radius` 无效）→ 直角也算票据；大数字字重被改 → 加 `letter-spacing` 保持气度。

---

## 通用三套

| 主题 | 气质 | 适合 |
|---|---|---|
| `magazine` | 编辑杂志，编号小标题 + 细分割线 | 稍正式的生活记录、长文 |
| `minimal` | 黑字白纸，居中细标题，极简 | 纯文字、以内容取胜 |
| `tech` | 深蓝 + 青色，等宽字体标签 | 技术随笔、工具分享 |

---

## 块的语义与版式解耦

**必须守住**：block 数据只描述「这是什么」，不含任何视觉值。

```json
{"type": "timeline", "items": [{"time": "08:20", "title": "出门", "desc": "地铁两站"}]}
```

不要写成 `{"type":"timeline","color":"#35657e","borderLeft":"2px"}`。
主题只覆盖颜色与装饰，块只描述结构。验收：同一份 doc 在 7 套主题下渲染，剥掉标签后文本必须完全相等。

---

## 新增一个场景包（3 步）

1. **加 token**：在 `themes.py` 的 `THEMES` 里加一项，至少给 `key/label/scene/accent/accent_soft/paper/font/body_size/body_color/line_height/accent_2/rule/radius/pad/gap/shadow`。
   新增字段一律用 `t.get(key, 默认值)` 读取，保证旧主题不炸。
2. **加块**：在 `render.py` 写 `b_xxx(b, t, idx)`，注册进 `BLOCKS`，并把名字加进 `SCENE_BLOCKS`。
3. **加自检样本**：把新块加进 `selftest.py` 的 `FIXTURE`，否则自检会报「未覆盖这些块型」。

然后跑：

```bash
python3 scripts/selftest.py --verbose
```

要求：结构闭合、图片数对、无 flex/grid/position、未知块型能降级。

---

## 微信里的失效清单

| 特性 | 状态 | 替代 |
|---|---|---|
| `display:flex` / `grid` | 被剥离 | `inline-block` + `font-size:0` + 百分比宽 |
| `position:absolute/fixed` | 被剥离 | 负 margin 叠压 |
| `::before` / `::after` | 不生效 | 真实字符（`❝` `·`）或空 `span` 画色块 |
| `transform: rotate` | 不稳 | 一律正放 |
| 渐变 `linear-gradient` | 不稳 | 纯色 + 1px 边框 |
| `calc()` | 不稳 | 定宽 + 负 `text-indent` |
| `box-shadow` | 可能被剥离 | **同时给 `border:1px solid`** |
| `<style>` / class / id | 被剥离 | 全部内联 |
| `table` | 保留良好 | 双栏、对齐优先用 table |
