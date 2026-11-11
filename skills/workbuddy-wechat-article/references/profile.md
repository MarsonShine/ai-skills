# 作者档案

档案只保存作者愿意长期保留的东西：署名、常写的题材、说话习惯、版式偏好和禁忌。它不是人物小传，也不应该由模型替作者填写。

## 字段

| 分组 | 字段 | 类型 | 说明 |
| --- | --- | --- | --- |
| `identity` | `name` | 1–24 字 | 必填，文章署名 |
| | `role`、`city`、`bio` | 文本 | 可选，≤40 / 20 / 80 字 |
| `family` | `ok_to_write` | 布尔 | 默认 `true`；`false` 时不写家人 |
| | `members[].relation` | 枚举 | `self`、`spouse`、`daughter`、`son`、`parent`、`pet` |
| | `members[].nickname` | 1–20 字 | 必填 |
| | `members[].age` | 0–120 整数 | 孩子必填 |
| `topics` | `frequent` | 1–12 项 | 必填，常写主题 |
| | `never`、`series` | 0–12 项 | 不写题材、系列名 |
| `voice` | `tone` | 枚举 | `warm`、`plain`、`witty`、`gentle`、`dry` |
| | `person` | 枚举 | `first`、`persona_third` |
| | `sentence_len` | 枚举 | `short`、`mixed`、`long` |
| | `catchphrases` | ≤10 项 | 口头禅，每项 ≤12 字 |
| | `reader_address` | ≤8 字 | 例：你们、大家 |
| | `humor` | 0–3 整数 | 幽默强度 |
| | `emoji` | 枚举 | `none`、`sparing`、`liberal` |
| | `signature`、`signoff` | 文本 | ≤16 / 40 字 |
| `typesetting` | `scene` | 枚举 | `family`、`travel`、`daily`、`anniversary`、`auto` |
| | `whitespace` | 枚举 | `tight`、`normal`、`airy` |
| | `para_len` | 枚举 | `short`、`mixed`、`long` |
| | `image_ratio` | 文本 | 例：`1:1`、`4:3` |
| | `prefer_blocks`、`forbid_blocks` | 数组 | 块类型名 |
| `taboo` | `hard_words`、`soft_words` | 数组 | 硬禁词、慎用词 |
| | `topics`、`avoid_tone`、`private` | 数组 | 不写题材、避免语气、隐私边界 |

字段写错会直接报错，并给出“字段 / 期望 / 实际”，不做静默纠错。

## 示例

```yaml
version: 1
identity:
  name: 阿柯
  role: 两个孩子的妈妈 / 自由插画师
  city: 杭州
  bio: 记录家里的碎日子，和一个总在改稿的自己
family:
  ok_to_write: true
  members:
    - {relation: daughter, nickname: 豆豆, age: 6, note: 爱问为什么}
    - {relation: son, nickname: 果果, age: 2}
    - {relation: spouse, nickname: 老周}
topics:
  frequent: [亲子日常, 手冲咖啡, 家居改造]
  never: [时政, 医疗建议, 投资理财]
  series: [豆豆语录, 一周咖啡]
voice:
  tone: warm
  person: first
  sentence_len: mixed
  catchphrases: ["说真的", "你别说"]
  reader_address: 你们
  humor: 1
  emoji: sparing
  signature: 阿柯 · 在杭州
  signoff: 下次见。
typesetting:
  scene: daily
  whitespace: airy
  para_len: short
  image_ratio: "1:1"
  prefer_blocks: [photo_polaroid, margin_note]
  forbid_blocks: [code]
taboo:
  hard_words: [赋能, 闭环, 降本增效]
  soft_words: [首先, 值得注意的是]
  topics: [疾病诊断, 学校具体名称]
  avoid_tone: [说教, 带货]
  private: [豆豆的学校, 家庭住址]
```

## 12 题问卷

1. 文章里署名是谁？
2. 身份和常待的城市？
3. 常写到的家人（称呼，孩子加年龄）？
4. 最常写的三个主题？
5. 哪些题材明确不写？
6. 语气：温暖 / 朴素 / 调侃 / 轻缓 / 克制？
7. 第一人称“我”，还是旁观口吻？
8. 句子偏短、混合还是偏长？
9. 常挂在嘴边的词？
10. 文末落款和告别语？
11. 版式留白：紧 / 正常 / 大？
12. 表情：不用 / 少量 / 常用？

每题可跳过，跳过项取默认值：`warm`、`first`、`mixed`、`sparing`、`normal`、`daily`。回答写成 JSON 后：

```text
python -X utf8 scripts/article.py profile --answers answers.json --save 文章目录/profile.yaml
```

短键名可用 `name`、`role`、`city`、`members`、`topics`、`never`、`tone`、`person`、`sentence_len`、`catchphrases`、`signature`、`signoff`、`whitespace`、`emoji`；也可以直接写 `voice.tone` 这样的完整路径。

## 加载顺序与隐私

`--profile` → 当前目录 `profile.yaml` → 文章目录 `profile.yaml` → `~/.config/workbuddy-wechat/profile.yaml` → `~/.wagent/profile.yaml`。命中即停。

- `family.ok_to_write: false` 时不写任何家庭成员。
- `taboo.private` 里的内容不进入文章、图注或公开预览。
- 不把档案文件放进文章目录之外的共享位置；不需要时删除本地副本。
