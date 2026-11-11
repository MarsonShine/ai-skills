---
name: workbuddy-wechat-article
description: "为个人或家庭生活类公众号写作、排版和交付草稿：初始化作者声音档案，检测并定点改写 AI 腔，按家庭、旅行、日常、纪念日四套场景生成预览，图片按四档画质处理并在上传后回读核验。适用于需要保留作者本人语气的公众号图文；不适用于批量搬运、纯营销文案或绕过作者确认直接群发。"
---

# 公众号人味写作与草稿助手

先保住作者的声音，再谈排版。默认流程是：作者档案 → 写块 → 自检 → 定点改写 → 预览 → 确认 → 草稿。每一步都输出 JSON，不要跳过自检直接发布。

运行环境为 Python 3.10+、Pillow 和 PyYAML；缺包时在技能目录运行 `python -m pip install -r requirements.txt`。不需要 Node.js。

## 0. 初始化作者档案

```text
python -X utf8 scripts/article.py profile --workdir 文章目录
```

返回 `profile: null` 时，按 `questions` 里的 12 个问题逐项询问作者，把回答写成 JSON，再运行：

```text
python -X utf8 scripts/article.py profile --answers 回答.json --save 文章目录/profile.yaml
```

读取顺序固定为 `--profile` → 当前目录 `profile.yaml` → 文章目录 `profile.yaml` → `~/.config/workbuddy-wechat/profile.yaml`。没有档案就按默认声部写，不要凭空编造家庭成员、城市或口头禅。字段、枚举和校验规则见 [作者档案](references/profile.md)。

写作时把 `profile` 输出的 `contract` 和 [文风合同](references/style-contract.md) 的 10 组正反例一起交给写作模型；不要只说“写得温暖一点”。

## 1. 写文章块

用 `blocks` JSON 描述内容，不写颜色、字号或宽度。块类型、场景专属块和微信降级规则见 [块与场景](references/blocks.md)。写的时候守住七件事：

- 从一个具体动作或画面切进去，不用“周末我们去了……”开场。
- 每个重要判断后面补一个可核实的细节：几点、什么天气、多少钱、谁的原话。
- 允许矛盾、允许没想明白；不要升华，不要替读者总结人生。
- 读者能自己补的留白，不解释。
- 结尾停在动作、一句对话，或一个未解决的问题。
- 图说事还是文说事，先定；图注只写用户提供的信息。
- 反复使用作者自己的词，不要为了避免重复换同义词。

只使用用户提供的事实。缺细节就在聊天里问，不要替作者补。`profile.yaml` 里的 `taboo.private` 和 `family.ok_to_write` 是硬约束。

## 2. 自检

```text
python -X utf8 scripts/article.py check --blocks 文章.json --profile 文章目录/profile.yaml --out 文章目录/voice.json
```

输出 `report`，其中包含 `scores`（`final`/`ai`/`human`/`band`）、`issues`、`clusters`、`keep`、`positive` 和 `targets`；`--out` 会把同一份报告写成文件。分档：85–100 人味足，70–84 可用，55–69 明显 AI 味，0–54 机器味重。`keep` 是“看着像问题但建议不动”的清单，改写前先读它。

规则和评分见 [AI 味检测](references/voice.md)。不要为了让分数好看删掉作者的短句、口头禅或未解决的情绪。

## 3. 定点改写

只改 `targets` 里的句子，一次一句。把下面的约束连同目标句、前后句和 `issues` 交给当前模型；提示词模板和四道校验见 [定点改写](references/rewrite.md)。

```json
[
  {"sentence_id": "3:text:1", "rewrite": "那天搬家，我第一次觉得，离开父母是件具体的事。", "reason": "拆掉对仗，换回当天的一个动作"},
  {"sentence_id": "5:text:0", "keep": true, "reason": "短句是人的呼吸，不是缺陷"}
]
```

```text
python -X utf8 scripts/article.py rewrite --blocks 文章.json --report 文章目录/voice.json --rewrites 改写.json --out 文章目录/blocks.2.json --changes 文章目录/changes.json
```

校验失败会进 `rejected`，原句保留。同一句只改一次；第二轮仍命中就冻结，写入理由。最多两轮，分数提升小于 2 就停。

## 4. 排版预览

```text
python -X utf8 scripts/article.py preview --blocks 文章目录/blocks.2.json --workdir 文章目录 --quality balanced --account 公众号AppID
```

生成 `preview.html`、`article.html` 和 `bundle.json`。先看 430px 预览：有没有横向溢出、图注是否跟图、段落是否挤在一起。场景可选 `family`、`travel`、`daily`、`anniversary`；`auto` 按日常处理。预览会顺带跑一次自检并把 `voice.json` 放进文章目录。

## 5. 图片

四档：`lossless`、`high`、`balanced`（默认）、`small`。顺序永远是先定尺寸、再定格式、最后才谈质量。正文图走 `media/uploadimg`，单图硬上限 1 MiB；封面走 `material/add_material`，上限 10 MiB。

上传后必须回读：`draft` 会把 CDN 上的图下载回来，用 Pillow 比对像素和字节，逐张输出 `lossless` 与原因。PNG 才可能真无损；JPEG 一律标 `lossless: false`。超限且无法在不降质前提下处理时返回 `exit 7` 和可选方案，绝不偷偷降质。细节见 [图片质量](references/images.md)。

```text
python -X utf8 scripts/article.py qc --blocks 文章.json --quality lossless
```

`qc` 不上传，只预演预处理结果。

## 6. 确认并写入草稿

1. 生成确认码并用一句话展示：账号、操作（新建/更新）、标题、版本、正文图和封面的 `lossless` 结论。

```text
python -X utf8 scripts/article.py confirm --workdir 文章目录 --account 公众号AppID --action draft
```

2. 等作者明确同意。一次同意只覆盖这一版正文、正文图和封面。正文、图片或账号变化后重新确认。
3. 写入：

```text
python -X utf8 scripts/article.py draft --workdir 文章目录 --account 公众号AppID --action draft --confirmed 确认码
```

更新已有草稿加 `--media-id 草稿ID --action update`。凭据从 `WECHAT_APPID` / `WECHAT_APPSECRET` 或 `~/.config/workbuddy-wechat/config.json` 读取，不写进文章目录。最后如实报告 `media_id`、逐图 `lossless`、草稿回读结果和后台入口，提醒作者在微信里预览实际裁切后手动发表。接口与恢复见 [微信草稿接入](references/wechat.md)。

## 输出约定

- 所有命令输出单个 JSON 对象；失败时 `ok:false`、`code`、`error`。
- 退出码：`0` 成功；`2` 参数/文件/配置错误；`4` 自检低于 `--fail-under`；`7` 无损档超限，需要作者选择；`8` 上传或回读失败。
- 绝不把绝对路径、AppSecret、access_token 或家庭成员隐私写进文章正文或公开预览。

## 参考

- [作者档案](references/profile.md)
- [文风合同与正反例](references/style-contract.md)
- [块与场景](references/blocks.md)
- [AI 味检测](references/voice.md)
- [定点改写](references/rewrite.md)
- [图片质量](references/images.md)
- [微信草稿接入](references/wechat.md)
