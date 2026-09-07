---
name: id-photo-maker
description: "制作报名用或可打印裁剪的证件照，支持尺寸、背景换色和打印排版。不用于普通人像修图或批量挑片。"
---

# ID Photo Maker

从现有照片制作标准尺寸成片和可打印裁剪页；仅在用户需要 AI 生成时调用 Liblib。

## 参数与路由

- 先用请求和现有资料确定尺寸、底色、构图。尺寸与底色无法确定时合并询问缺口；普通证件照构图默认 `standard`，已有明确生成请求时不再确认是否生图。
- 本地照片或普通图片 URL 走本地处理，不索取 Liblib 凭证。URL 由处理脚本下载。
- 只有文字且没有照片时，区分用户要生成形象还是处理真实照片；意图不明才询问。
- Liblib 图生图需要公网图片 URL。没有 URL 时说明缺口，不擅自上传本地照片，也不静默改用其他生成服务。
- 默认交付成片与 A4、6 寸打印页；用户只要报名上传图或指定一种打印页时，按其要求交付。

## 执行

使用可用的 Python 3.11+；本地处理依赖 Pillow、rembg，见 `requirements.txt`。下列路径中的 `{baseDir}` 是当前技能目录，不是固定的用户安装目录。

```text
python "{baseDir}/scripts/process_local_photo.py" "<photo-path-or-url>" --size 1寸 --background white --framing standard --output-dir "<processed-dir>"
python "{baseDir}/scripts/render_print_sheet.py" --photo "<processed-dir>/id-photo.png" --size 1寸 --pages a4,6inch --output-dir "<print-dir>"
```

参数示例应替换为用户规格。需要自定义尺寸或构图时，读取 `references/size-presets.md`；需要生成、特殊路由或打印细节时，读取 `references/workflow-rules.md`。

生成入口为 `scripts/generate_via_liblib.py text2img` 或 `img2img`，运行 `--help` 获取参数。用简洁英文 prompt 保留用户需求，生成后继续处理与排版。

## 凭证

只在调用 Liblib 时检查凭证是否配置，不输出密钥值。生成脚本依次使用显式参数、`--env-file` 指定的文件（默认当前技能根目录 `.env.local`）、环境变量 `LIBLIB_ACCESS_KEY` / `LIBLIB_SECRET_KEY`。

缺失时请用户通过本地环境或凭证配置入口补齐；不要把密钥写入示例、日志或报告。仅在用户要求保存凭证时使用 `scripts/credential_store.py` 的保存功能或 `--save-credentials`；已存在的保存授权无需再次询问。只有排查签名或请求问题才读取 `references/liblib-auth.md`。

## 交付与验证

检查成片尺寸、底色、裁切，以及打印页的物理尺寸与排版。标准产物为 `id-photo.png`、`metadata.json`，以及所选打印页 `print-a4.html`、`print-6inch.html` 和 `index.html`；报告实际生成的文件。打印时使用 100% 比例，关闭浏览器缩放适配。

保留源照片；不声称通用预设已满足某个报名系统的专门要求。无法完成时说明实际失败步骤与缺失条件，保留已完成的结果。
