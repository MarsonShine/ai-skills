---
name: id-photo-maker
description: "根据文字、参考图、公网图片 URL 或本地照片制作可直接打印裁剪的证件照。只要用户提到证件照、报名照、护照照、白底/蓝底/红底换底、1寸/2寸、证件照排版、证件照打印、或想把普通照片变成证件照，都应使用这个 skill。默认优先处理用户已有照片；只有缺图或用户明确要求时，才调用 Liblib 的文生图或图生图。"
compatibility: "Works best with bash and Python 3.11+. Liblib API calls use only Python stdlib. Photo processing needs Pillow and rembg, ideally inside ~/.copilot/skills/id-photo-maker/.venv."
---

# ID Photo Maker

把证件照制作变成稳定、可重复的执行流程：先判断输入来源，再收集缺失参数，然后按需走 Liblib 生图或本地照片处理，最后输出可直接打印裁剪的静态排版页。

## Default operating mode

- 默认优先使用用户已有照片。
- 只有用户没有可用照片，或明确说“帮我生一张 / 图生图 / AI 生成”时，才调用 Liblib。
- 用户提供本地照片时，不要擅自走 Liblib 图生图。
- 用户提供公网图片 URL 时，先下载到本地；除非用户明确要求图生图，否则仍按本地照片流程处理。
- 如果用户想用本地照片做 Liblib 图生图，先明确告知：Liblib 需要公网可访问 URL。没有公网 URL 时，不要私自上传到第三方图床。
- 输出默认是可打印裁剪页，不是只给单张图。能做时，优先同时生成 `A4` 和 `6寸` 两种打印页。

## Information to collect

必须收集：

- 证件照尺寸 / 规格
- 背景色
- 构图范围

按需收集：

- 是否真的需要 AI 生图
- 是否要使用参考图控制构图
- 是否已有 Liblib `AccessKey` / `SecretKey`
- 是否同意把 AK / SK 保存到本地 `.env.local`

如果缺少这些信息，主动追问。优先一问一答，不要一口气抛太多问题。

## Decision flow

1. **文字描述，没有现成照片**
   - 询问尺寸、底色、构图范围。
   - 确认是否需要 AI 生图。对纯文字输入，通常答案是“需要”。
   - 如需 Liblib，检查 AK / SK；缺失就向用户要，并询问是否保存到本地。
   - 将中文需求整理为简洁英文 prompt，再运行：
     - `scripts/generate_via_liblib.py text2img ...`
   - 生图完成后，再运行：
     - `scripts/process_local_photo.py ...`
     - `scripts/render_print_sheet.py ...`

2. **本地照片**
   - 默认直接做照片处理，不要先问 AK / SK。
   - 运行：
     - `scripts/process_local_photo.py ...`
     - `scripts/render_print_sheet.py ...`
   - 只有当用户明确要求 Liblib 图生图时，才继续确认是否有公网图片 URL；没有就建议改回本地处理流程。

3. **公网图片 URL**
   - 如果用户只是想做证件照：下载到本地后直接走照片处理。
   - 如果用户明确要求 Liblib 图生图：可把这个 URL 直接作为 `sourceImage` 传给 Liblib，成功后再做后处理和排版。

## Prompt construction rules for Liblib

- Liblib 的 `prompt` 使用纯英文。
- 先保留用户的真实意图，再转成简洁英文，不要塞太多花哨画风词。
- 对证件照场景，默认强调：
  - `clean studio lighting`
  - `front-facing person`
  - `realistic face`
  - `formal ID photo`
  - `centered composition`
  - `plain background`
  - `high detail`
  - `no watermark`
- 如果用户给了参考图或想保持姿态 / 构图，再按需加：
  - `controlType: depth | pose | line | IPAdapter`
  - `controlImage: <public URL>`

## Credential handling

- 只在需要调用 Liblib 时才检查凭证。
- 优先从以下位置读取：
  1. 命令行参数
  2. `~/.copilot/skills/id-photo-maker/.env.local`
  3. 当前 shell 环境变量
- 如果仍缺失：
  - 向用户索要 `AccessKey` 与 `SecretKey`
  - 只有在用户明确同意时，才以 `LIBLIB_ACCESS_KEY=...` / `LIBLIB_SECRET_KEY=...` 的形式写入 `.env.local`
- 不要在普通输出里回显 `SecretKey`。

## Recommended commands

如果 skill 目录有 `.venv/bin/python`，优先用它；否则用 `python3`。

### 文生图

```bash
python3 ~/.copilot/skills/id-photo-maker/scripts/generate_via_liblib.py \
  text2img \
  --prompt "front-facing young woman, formal chinese id photo, clean studio light, realistic face, centered composition, plain background, high detail, no watermark" \
  --aspect-ratio portrait \
  --output-dir /tmp/id-photo-run/generated
```

### 图生图

```bash
python3 ~/.copilot/skills/id-photo-maker/scripts/generate_via_liblib.py \
  img2img \
  --prompt "formal id photo, realistic face, centered composition, clean studio light, no watermark" \
  --source-image-url "https://example.com/reference.png" \
  --output-dir /tmp/id-photo-run/generated
```

### 照片处理

```bash
python3 ~/.copilot/skills/id-photo-maker/scripts/process_local_photo.py \
  /tmp/id-photo-run/generated/liblib-1.png \
  --size 1寸 \
  --background white \
  --framing standard \
  --output-dir /tmp/id-photo-run/processed
```

### 打印排版

```bash
python3 ~/.copilot/skills/id-photo-maker/scripts/render_print_sheet.py \
  --photo /tmp/id-photo-run/processed/id-photo.png \
  --size 1寸 \
  --pages a4,6inch \
  --output-dir /tmp/id-photo-run/print
```

## Output expectations

默认交付：

- `id-photo.png`：标准尺寸成片
- `metadata.json`：尺寸、背景、构图、来源与导出信息
- `print-a4.html`
- `print-6inch.html`
- `index.html`：打印页入口

## Resources in this skill

- `scripts/id_photo_common.py` - shared size presets, color parsing, and download helpers
- `scripts/credential_store.py` - `.env.local` credential read/write
- `scripts/liblib_client.py` - Liblib API signing, request, polling, and download
- `scripts/generate_via_liblib.py` - CLI for text2img / img2img
- `scripts/process_local_photo.py` - local / URL photo processing, background replacement, and export
- `scripts/render_print_sheet.py` - A4 / 6寸 printable HTML sheet generation
- `references/size-presets.md` - supported presets and physical dimensions
- `references/workflow-rules.md` - routing, prompt, and questioning rules
- `references/liblib-auth.md` - AK/SK signing model and request rules
- `assets/print.css` - print-safe stylesheet
- `requirements.txt` - Python dependencies
