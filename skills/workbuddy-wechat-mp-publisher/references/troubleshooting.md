# 排障手册

按症状查。每条都是「症状 → 原因 → 命令级修复」。

---

## 凭据与网络

### `check` 返回 exit 3 / `errcode -3`

**原因**：`WX_APPID` 或 `WX_SECRET` 没配。

```bash
export WX_APPID=wx...
export WX_SECRET=...
python3 scripts/wx_publish.py check
```

或写配置文件（自动 0600）：

```json
// ~/.config/wechat-mp/config.json
{"appid": "wx...", "secret": "..."}
```

### `check` 返回 exit 4 / `errcode 40164`

**原因**：出口 IP 不在白名单。

JSON 里有 `exit_ip`，直接给用户：

> 把 `1.2.3.4` 加进「公众号后台 → 设置与开发 → 基本配置 → IP 白名单」，保存后重试。

**注意**：云函数、容器、CI 的出口 IP 会漂移。今天加白明天就失效，这不是配置错。

### `errcode 40001` 反复出现

**原因**：别处用了 `/cgi-bin/token`，把 token 踢掉了。

**修复**：删掉缓存强制重取一次，并检查是否有其他工具在用普通 token。

```bash
rm -f ~/.cache/wagent/token.json
```

### `errcode 40125`

**原因**：AppSecret 错，最常见是复制时带了空格或换行。

**修复**：后台重置 AppSecret，重新复制，别用「复制为富文本」。

---

## 草稿

### `errcode 40007`

**原因**：`thumb_media_id` 失效（封面被删）或 `media_id` 不存在。

**修复**：

```bash
python3 scripts/wx_publish.py draft --force-new ...
```

### `errcode 40008`

**原因**：标题超 64 字符，或字段类型不对。

**修复**：`wx.validate_article()` 会在提交前拦。看到 `标题 N 字，超过微信上限` 就改短，**不要靠截断**——截断后的标题读起来是断的。

### `errcode 53404`

**原因**：草稿箱有数量上限，满了。

**修复**：删旧草稿，或复用已有的（同内容重跑会自动 `update`）。

### 提交成功但草稿里图片空白

**原因**：`content` 里是本地路径或外链，被过滤了。

**修复**：必须走 `draft` 子命令，它会上传图片并替换成 `mmbiz.qpic.cn`。不要手拼 `<img src="本地路径">`。

**验证**：

```bash
python3 scripts/wx_publish.py status --media-id <id>
# images_on_cdn 应等于你提交的图片数，为 0 就是全被过滤了
```

### exit 6 + `mismatch`

**原因**：回读到的内容和提交的不一致。

**看这几个字段**：

- `all_images_in_content: false` → 图片被过滤
- `content_len_remote` 远小于 `content_len_local` → 内容被截断（可能超 20000 字符）

---

## 图片

### exit 7 + `blocked`

**原因**：图片超 1MB 且不能在不降质的前提下处理。

JSON 的 `reason` 里已经给了三个选项：

1. 缩到 1280 宽（会降尺寸，观感通常没差别）
2. 改 `--quality high`（会重编码）
3. 换图

**不要自己决定降质**。问用户。

### `qc` 说 `lossless: true`，但线上看起来糊

**原因**：`qc` 只是本地预演，不含服务端压缩。

**修复**：看 `draft` 返回的 `quality[]` 里的 `cdn_px` 和 `cdn_bytes`——那才是真相。`lossless: false` 时会带 `loss_reason`。

### PNG 传不上去

**原因**：>1MB。3000×2000 的照片存 PNG 常 8–15MB。

**修复**：照片本来就不该用 `lossless`。用默认的 `balanced`。

---

## 排版

### 有序列表的序号看不见

**原因**：`text-indent:-28px` 被 `inline-block` 的标记 span 继承，字符被画到盒子外。

**修复**：标记 span 上加 `text-indent:0`。（已在 `render.py` 修掉，若自行改写块要注意。）

### 双图并排只出一张

**原因**：`<img>` 的 `style` 属性引号没闭合，第二个 `<img src="` 被吞进属性值。

**修复**：跑 `selftest.py`，它会报「属性被污染」。

### 票根右栏掉到下面

**原因**：`width:66%` + `padding:16px` 是 content-box，两栏加起来超 100%。

**修复**：双栏改 `table`。

### 内容在手机上左右被裁

**原因**：横向溢出。

**检查**：

```python
document.documentElement.scrollWidth - document.documentElement.clientWidth  # 必须为 0
```

常见来源：`width` 用了固定 px 超过 414、`inline-block` 定宽加 padding、`margin` 负值过大。

### 分隔符 / 装饰点几乎看不见

**原因**：用了 `sub_color`（浅灰）或小字号字符 `· · ·`。

**修复**：改用实心圆点 span，颜色用主题色的半透明（`rgba(...)`），尺寸 4px 起。

---

## 内容诊断

### 人写的好文章被判成「明显 AI 味」

**先看 `keep[]`**：如果被判罚的句子细节密度 ≥2.0，是误伤。

**调整方式**（按优先级）：

1. 把该处词加进 `profile.topics.write` 白名单
2. 在 `profile.taboo.hard_words` 里删掉误判的词
3. 用户明确说「我就要这么写」→ 接受，记入 `keep[]`，理由写「用户明确保留」

**不要争辩第二次。**

### 改完之后反而更假

**原因**：改出了另一种模板化口语。

**表现**：所有句子都变短、都变成口语、都在避免排比——整齐得像另一种模板。

**修复**：

- 停掉第二轮重写（`--max-rounds 1`）
- 检查 `keep[]` 是否被尊重：短句、毛边、矛盾情绪属于「人写的迹象」，不该修掉
- 让用户自己改那几句，往往比模型改得好

### `rewrite: null` 但 `recommend: rewrite`

**原因**：没配 `LLM_API_KEY`，无法调用模型。

**修复**：要么配 key，要么把 `issues` 原样交给用户改。`voice` 子命令不配 key 也能用，只是不出改写。

---

## 人格文件

### exit 8 + `details[]`

**原因**：`profile.yaml` 字段非法。报错格式是「字段 / 期望 / 实际」，例如：

```
voice.tone: 期望 warm/plain/witty/gentle/dry 之一，实际 'warmm'
```

**修复**：按提示逐条改。**系统不会静默纠错**——写错 `warmm` 却按 `warm` 跑，用户永远不知道自己写错了。

### 找不到 profile

**查找顺序**：`--profile` → `WECHAT_MP_PROFILE` → 文章目录 → `~/.wagent/profile.yaml`。

**修复**：显式传 `--profile`，或放一份到 `~/.wagent/profile.yaml`。

---

## 快速自检

```bash
python3 scripts/selftest.py --verbose   # 渲染层：结构、图片数、禁用 CSS、降级
python3 scripts/wx_publish.py check     # 凭据与 IP
python3 scripts/wx_publish.py qc --images ./photos --quality lossless   # 图片会发生什么
```

三个都过了，再跑 `draft`。
