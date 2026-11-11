---
name: workbuddy-wechat-mp-publisher
description: 把用户给的照片和一段粗略文案，按账号人格与场景主题排成微信公众号图文，先做去 AI 味诊断再落进草稿箱、回读校验后交付 media_id，最后的「发表」由人手动完成。当用户提到公众号排版、图文排版、发公众号、生成公众号草稿、把这些照片发到公众号、看看在公众号上是什么效果、微信推文、草稿箱、记录孩子/家庭/旅行/纪念日时使用。
allowed-tools: Read, Write, Bash, Glob
---

# 公众号图文排版发布

**只做到草稿箱，永不自动发表。** 这是硬边界：公众号是用户的脸面，最后一步必须由人点。

## 能力边界

做：粗文案 → 结构化成 blocks → 主题排版 → 去 AI 味诊断 → 定点重写 → 上传图片 → 写草稿 → 回读校验。
不做：自动发表、定时群发、多图文合辑、AI 配图、数据统计、评论管理。

## 第 0 步：确认账号人格（有就一句话过，没有才问）

按顺序找 `profile.yaml`：`--profile` 参数 → 环境变量 `WECHAT_MP_PROFILE` → 文章所在目录 → `~/.wagent/profile.yaml`。

```bash
python3 <skill>/scripts/wx_publish.py init                  # 没有文件：拿到问卷，在对话里问用户
python3 <skill>/scripts/wx_publish.py init --out a.yaml --answers answers.json   # 问完落盘
python3 <skill>/scripts/wx_publish.py init --template --out ~/.wagent/profile.yaml  # 让用户自己填
```

- **已有**：只确认一句「还是按『阿柯 · 日常随笔』来写吗」，不要重复问。
- **没有**：告诉用户「这一步值得花 3 分钟，之后每篇都省事」，然后把 `questions` 逐条问。允许跳过，跳过的取默认值。
- 用户改了 YAML 就让下游自动读到，不需要重跑问卷。

人格决定六件事：语气、人称、句子节奏、口头禅、落款、禁用词。写进 prompt 之前先拼成「文风合同」（`profile.contract()`），不是「写得温暖一点」这种废话。

## 第 1 步：前置检查

```bash
python3 -c "import requests, PIL, yaml" || pip3 install requests Pillow PyYAML
python3 <skill>/scripts/wx_publish.py check
```

| 结果 | 动作 |
|---|---|
| `ok: true` | 继续 |
| exit 3 / `errcode -3` | 缺 `WX_APPID`/`WX_SECRET`。让用户设环境变量，或写 `~/.config/wechat-mp/config.json`（0600） |
| exit 4 / `errcode 40164` | IP 未加白。JSON 里有 `exit_ip`，让用户把它加进「设置与开发 → 基本配置 → IP 白名单」 |
| exit 5 / `48001` | 账号无该接口权限。**未认证订阅号也能用草稿箱**，只有 `freepublish` 不行——本 skill 不调它 |

用户还没准备好凭据也可以先做排版：`preview` 和 `voice` 都不需要凭据。

## 第 2 步：收料

要三样东西：**图片绝对路径**、**一段原始文案**、**主题**。

- 图片可以是多个文件，也可以直接给目录。相对路径会在入口处 resolve 成绝对路径。
- 文案原文照收，不用整理。用户给的错别字、口语、跳跃的句子都要留着——那正是人味。
- 主题没说就按内容判断并**说明理由**：「这篇有孩子对话、有具体时间，建议用家庭的暖色，拍立得和童言卡会好看」。
- 顺手确认画质诉求：截图/图表/设计稿 → `--quality lossless`；手机拍的 → `default balanced`。

如果文案信息太少（只有一两句话、没有场景），**先问，不要写**。可以按 `references/writing-craft.md` 的七问挑 3–4 条问：这件事从哪个瞬间写起、几点、当时天气、有没有一句原话。

## 第 3 步：生成与诊断（**必须停下来给用户看**）

```bash
python3 <skill>/scripts/wx_publish.py preview \
  --images ./photos --text-file copy.txt --scene family --quality balanced
```

返回 JSON 里有 `preview_path`、`title`、`voice.scores`、`warnings`。

- **默认保真**：只分节、配图、排版，一个字不改。
- 加 `--rewrite` 才让模型写标题、摘要、过渡句，且禁止编造事实。
- 把 `preview_path` 用 `present_files` 给用户看，同时报告 `voice.scores`：

| `final` | 含义 | 动作 |
|---|---|---|
| ≥85 | 人味足 | 直接进第 5 步 |
| 70–84 | 可用 | 把 `issues` 和 `keep` 一起给出，问要不要改 |
| 55–69 | 明显 AI 味 | 建议重写 |
| <55 | 机器味重 | 必须重写，或让用户补细节 |

`recommend: rewrite` 时不要只看分数——结尾升华这种问题只扣 10 分，但读者一眼能看出来。

**报告时必须带上 `keep[]`**：那是「看着像问题但建议保留」的地方（短句、毛边、没解决的矛盾）。不说明的话，用户会以为你没看见。

## 第 4 步：定点重写（条件触发）

```bash
python3 <skill>/scripts/wx_publish.py voice --images ./photos --text-file copy.txt --max-rounds 2
```

只有配了 `LLM_API_KEY` 才会真的调用模型；没有就只出诊断，并明确告诉用户「这几句需要你自己改」。

改完按四段式呈现，不要只丢一句「已优化」：

1. **分数变化**：`72.8 → 84.0`
2. **逐条改动**：原句 / 改句 / 为什么 / 问题类型
3. **保留项及原因**：哪些地方看着像问题但没动，以及为什么
4. **需要你补的细节**：`need_your_detail` 里的项。AI 编不出真实细节，只能标出来让人补

被 `rejected` 的改写要看原因：一般是模型想加事实、或想把一句拆成两句，已自动丢弃。

## 第 5 步：预览确认（**必须停下来**）

把 `preview.html` 给用户看，明确问三件事：版式对不对、图的位置对不对、标题行不行。

不要跳过这一步直接 `draft`。草稿一旦写进去，改稿虽然能 `update`，但用户的工作流已经被打断了。

## 第 6 步：落草稿并交付

```bash
python3 <skill>/scripts/wx_publish.py draft \
  --images ./photos --text-file copy.txt --scene family --quality balanced
```

返回里必须交代清楚：

- `media_id`：草稿唯一标识
- `checks`：回读校验结果，全 true 才算成功
- `quality[]`：每张图的 `src_px` / `cdn_px` / `lossless`。`lossless:false` 时把 `loss_reason` 原文给用户，让他自己决定换不换图
- **`next`**：去「草稿箱」核对，确认后手动点发表

改稿用 `update --media-id <id>`。同内容重跑会返回 `reused: true`，不会堆重复草稿。

## 失败回退

| 现象 | 原因 | 怎么做 |
|---|---|---|
| exit 2 `标题 N 字，超过微信上限 64 字` | 标题太长 | 让用户改短，**不要静默截断** |
| exit 3 | 凭据错 | 检查 `WX_SECRET`，注意别带空格 |
| exit 4 + `exit_ip` | IP 未加白 | 把 `exit_ip` 加白，重启后重试 |
| exit 5 `40007` | 缩略图 media_id 失效 | 重新 `draft --force-new` |
| exit 6 + `mismatch` | 回读到的内容与提交的不一致 | 通常是被过滤了图片，检查 `all_images_in_content` |
| exit 7 + `blocked` | 图片超 1MB 且不能无损处理 | 给三个选项：缩到 1280 宽 / 改 `high` 档 / 换图。**绝不偷偷降质** |
| exit 8 + `details[]` | profile.yaml 字段非法 | 按「字段 / 期望 / 实际」逐条改，不猜 |
| 正文图不显示 | 本地路径没换成 CDN URL | 必须走 `draft`，它会上传并替换；不要手拼 `<img src="本地路径">` |

## 深入阅读

按需读，不要一次全读：

- `references/writing-craft.md` —— 七条写作决策、文风合同模板、10 组 ❌/✅ 正反例
- `references/voice-rules.md` —— 24 条 AI 特征、中文本土化阈值、**不要误伤**
- `references/scenes.md` —— 4 个场景包的适用内容、专属块、失效降级
- `references/editor-html-rules.md` —— 微信编辑器会剥离什么、为什么不能用 flex
- `references/wechat-api.md` —— 接口、配额、字段上限、错误码
- `references/image-quality.md` —— 为什么 PNG 能无损、1MB 上限怎么绕
- `references/troubleshooting.md` —— 症状 → 原因 → 命令

## 交付前的自检

```bash
python3 <skill>/scripts/selftest.py      # 7 套主题 × 30 类块的结构校验
```

发布前必须全部通过：标签闭合、图片数对得上、没有 flex/grid/position、没有模板占位符残留。
