---
name: photo-selector
description: "从本地照片批量挑片、比较相似照片、排序或生成联络表，选出待精修作品。不用于生成或编辑单张图片。"
---

# Photo Selector

从本地照片中选出值得精修的作品，交付终选名单与所需联络表；完整挑片任务默认把终选 JPG 复制到源目录下的 `精修` 文件夹。

## 工作方式

1. 确定素材范围、用途与用户要的交付物。只要求联络表、排名或比较时完成该项，不自动复制终选片。
2. 盘点 JPG/JPEG 和配套 RAW，检查输出目录是否已有内容。批量素材生成带文件名的联络表；少量图片可以直接看原图。
3. 按用途比较清晰度、曝光、主体表达、构图与场景代表性。人像或亲子纪念照需要审美细则时，读取 `references/selection-rubric.md`；产品、建筑等题材按其用途判断。
4. 压缩重复连拍，通常保留最强的 1–2 张；用户要求动作序列或故事完整性时据此保留。候选难以区分才生成更大联络表，关键竞争帧和边界帧必须复核原图。
5. 交付终选名单与简短取舍依据。完整挑片时复制终选 JPG；仅在用户要求时补拷 RAW。

## 联络表工具

macOS 默认使用 JXA + AppKit；Linux / Windows 使用 Python 3 + Pillow。包装器会优先使用技能内已有的 `.venv`。

```text
bash "{baseDir}/scripts/make_contact_sheets.sh" "<photos-dir>" "<sheets-dir>" 4 4 480 360
pwsh -File "{baseDir}/scripts/make_contact_sheets.ps1" "<photos-dir>" "<sheets-dir>" 4 4 480 360
```

按当前平台选择一个入口。参数依次为输入目录、输出目录、列数、行数、单格宽高；可追加候选名单路径（每行一个文件名）。需要放大候选时可用 `3 3 640 480`。

缺少 Pillow 时使用 `python -m pip install pillow`，遵循当前环境的安装权限。后端实现为 `scripts/contact_sheet.jxa` 与 `scripts/contact_sheet_pillow.py`；Bash 包装器支持 `PHOTO_SELECTOR_BACKEND=macos-jxa|python-pillow` 和 `PHOTO_SELECTOR_PYTHON`。

## 源片保护

不删除、移动或覆盖源片，不批量重命名源片，除非用户明确要求重命名。保留已有 `精修` 内容，重名时跳过或使用新名称并报告，不清空目录。

交付实际生成的联络表、终选名单、复制位置与张数。不要在未查看图片时宣称已完成审美筛选。
