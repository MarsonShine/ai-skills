# 微信编辑器的 HTML 规则

公众号正文不是网页，是一个**只认内联样式的富文本片段**。写错的表现通常不是报错，而是「看起来还好，发出去变形」。

## 会被直接剥掉

| 写法 | 结果 |
|---|---|
| `<style>` 标签 | 整段删除 |
| `class` / `id` | 属性删除，样式不生效 |
| `<script>` / 事件属性 | 删除 |
| 外部 CSS、`@import` | 删除 |
| `<link>` | 删除 |

**所有样式必须内联在 `style="..."` 上。**

## 布局属性

| 属性 | 状态 | 替代方案 |
|---|---|---|
| `display:flex` | 剥离或不生效 | `inline-block` + `font-size:0` + 百分比宽 |
| `display:grid` | 同上 | 同上，或用 `table` |
| `position:absolute/fixed` | 剥离 | 负 `margin` 叠压 |
| `position:relative` | 不稳 | 避免 |
| `float` | 部分保留但不稳 | `inline-block` |
| `transform` | `rotate` 不稳 | 一律正放 |
| `calc()` | 不稳 | 算好固定值 |
| `::before` / `::after` | 不生效 | 真实字符或空 `span` 画色块 |

## 能用的

- `display: block / inline / inline-block / table / table-cell`
- `margin`（含负值）、`padding`、`width/height`（px 或 %）
- `border`（含 `dashed/dotted`）、`border-radius`
- `background-color`；`background-image` 支持但**渐变不稳**，慎用
- `color`、`font-size`、`font-weight`、`font-family`、`line-height`、`letter-spacing`、`text-align`、`text-indent`、`vertical-align`
- `box-shadow`（**可能被剥离，必须同时给 `border` 兜底**）
- `table` 全部特性，包括 `border-collapse`

## 三个高频坑

### 1. `text-indent` 会被 `inline-block` 继承

给 `<section>` 设了 `text-indent:-28px` 做悬挂缩进，里面的 `<span style="display:inline-block">01</span>`
会**继承这个负缩进**，把字符画到盒子左侧外面，被裁掉。

现象：序号完全不可见，但 DOM 里尺寸正常。

修法：在标记 span 上显式写 `text-indent:0`。

### 2. `inline-block` 定宽 + 内边距会撑破 100%

`width:66%` + `padding:16px` 是 content-box，实际占宽 `66% + 32px`。
两栏加起来超过容器，第二栏就换行——看起来像「右栏掉到下面去了」。

修法：双栏一律用 `table`，或把 padding 算进百分比。

### 3. 属性引号漏闭合会吞掉下一个标签

```html
<img src="a.jpg" style="width:49%;margin:0 0 2%;>   ← style 的引号没闭合
<img src="b.jpg" style="width:49%;">
```

浏览器会把第二张图的 `src="` 当成第一张 `style` 属性值的一部分，结果**双图只出一张**。

`selftest.py` 会检查属性值里是否混入 `<` 或 `src=`，就是为抓这个。

## 图片

| 写法 | 结果 |
|---|---|
| `<img src="https://mmbiz.qpic.cn/...">` | ✅ 正常 |
| `<img src="本地路径">` | ❌ 被过滤，草稿里空白 |
| `<img src="外链图床">` | ❌ 多数被过滤或加防盗链 |
| `<img src="data:image/png;base64,...">` | ❌ 被删 |
| `<img style="width:100%">` | ✅ 推荐 |

**正文图必须先走 `media/uploadimg` 换成 `mmbiz.qpic.cn` 的 URL。**

## 正文容器尺寸

- 正文区最大宽 **677px**，实际手机屏多在 375–430px。
- 本地预览按 **430px** 验收，能覆盖绝大多数机型。
- 段落文字左右各留 16px 左右比较舒服（微信本身有 padding，别叠太多）。

## 验收方法

```bash
python3 scripts/selftest.py --verbose
```

检查四件事：标签闭合、图片数量、禁用 CSS、模板占位符残留。

再加一步人工：

```python
# 430px 视口截图，量一下有没有横向溢出
document.documentElement.scrollWidth - document.documentElement.clientWidth  # 必须为 0
```

## 为什么不用第三方排版库

市面上的「一键排版」多数输出带 class 的 HTML + 一段 `<style>`。
粘进公众号后台后 `<style>` 被删，只剩裸标签——预览好看，发出去全乱。

本 skill 的做法是**直接产内联样式**，所见即所得，不依赖任何运行时。
