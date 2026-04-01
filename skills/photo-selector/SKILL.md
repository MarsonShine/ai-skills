---
name: photo-selector
description: "从本地照片文件夹中按专业摄影标准筛选出值得精修的照片。先生成联络表，再做多轮挑片，最后把终选片复制到“精修”文件夹。macOS 默认走原生 JXA，Linux 和 Windows 可走 Python Pillow 后端。"
compatibility: "macOS uses bash + osascript + JXA + AppKit by default. Linux and Windows use Python 3 + Pillow. A PowerShell wrapper is included for Windows."
---

# Photo Selector

把本地照片挑片任务做成稳定、可复用的执行流程：先盘点素材，再生成联络表完成大范围初筛，随后压缩连拍、复核原图，最后把终选片复制到同级 `精修` 文件夹。默认直接执行，不停留在抽象建议。

## Default operating mode

- 默认做完整挑片，而不是只给标准。
- 永远不要删除、移动、覆盖原片。
- 默认只复制终选 JPG 到 `精修` 文件夹。
- 如果用户明确要求，再补拷配套 RAW。
- 同一连拍只保留最强的 `1-2` 张，避免冗余。
- 关键竞争帧必须看原图，不要只靠缩略图定胜负。

## Platform compatibility

- **macOS**
  - 默认后端：`osascript + JXA + AppKit`
  - 推荐命令：
    - `bash ~/.copilot/skills/photo-selector/scripts/make_contact_sheets.sh "/path/to/photos" "/path/to/contact_sheets_16" 4 4 480 360`
- **Linux**
  - 后端：`Python 3 + Pillow`
  - 推荐命令：
    - `bash ~/.copilot/skills/photo-selector/scripts/make_contact_sheets.sh "/path/to/photos" "/path/to/contact_sheets_16" 4 4 480 360`
- **Windows**
  - 后端：`Python 3 + Pillow`
  - 推荐命令：
    - `pwsh -File "$HOME/.copilot/skills/photo-selector/scripts/make_contact_sheets.ps1" "C:\path\to\photos" "C:\path\to\contact_sheets_16" 4 4 480 360`
  - 如果在 Git Bash 或 WSL 下运行，也可以继续使用 `make_contact_sheets.sh`。

依赖说明：

- macOS 原生后端不需要 Pillow。
- Linux / Windows 需要安装 Pillow：
  - `python -m pip install pillow`
- 当前 skill 目录如果存在 `.venv`，包装脚本会优先使用其中的 Python。
- `make_contact_sheets.sh` 会自动选后端，也可以用环境变量强制指定：
  - `PHOTO_SELECTOR_BACKEND=macos-jxa`
  - `PHOTO_SELECTOR_BACKEND=python-pillow`
  - `PHOTO_SELECTOR_PYTHON=/custom/python`

## Workflow

1. 盘点素材
   - 统计 JPG、JPEG、RAW 的数量和分布。
   - 确认工作目录、输出目录，以及是否已有 `精修` 文件夹。

2. 生成第一轮联络表
   - 对整批 JPG 生成 `4x4` 联络表。
   - 文件名必须显示在每张缩略图下方，方便快速回指原图。
   - 推荐使用：
      - `bash ~/.copilot/skills/photo-selector/scripts/make_contact_sheets.sh "/path/to/photos" "/path/to/contact_sheets_16" 4 4 480 360`
      - Windows PowerShell: `pwsh -File "$HOME/.copilot/skills/photo-selector/scripts/make_contact_sheets.ps1" "C:\path\to\photos" "C:\path\to\contact_sheets_16" 4 4 480 360`

3. 第一轮初筛
   - 先抓“大方向正确”的帧：
     - 情绪自然
     - 主体明确
     - 光线可用
     - 构图完整
     - 有纪念性或故事感
   - 第一轮宁可多留，不要过早淘汰边界好片。

4. 第二轮压缩
   - 把候选名单写入一个文本文件，每行一个文件名。
   - 用更大的 `3x3` 联络表复看候选：
      - `bash ~/.copilot/skills/photo-selector/scripts/make_contact_sheets.sh "/path/to/photos" "/path/to/round2_sheets" 3 3 640 480 "/path/to/candidate_list.txt"`
      - Windows PowerShell: `pwsh -File "$HOME/.copilot/skills/photo-selector/scripts/make_contact_sheets.ps1" "C:\path\to\photos" "C:\path\to\round2_sheets" 3 3 640 480 "C:\path\to\candidate_list.txt"`
   - 在同组连拍里压掉弱帧，只保留真正最强的那一两张。

5. 原图复核
   - 对边界帧直接查看原图。
   - 重点检查：
     - 是否实焦
     - 是否闭眼或半闭眼
     - 表情是否真的成立
     - 高光是否爆掉
     - 背景是否有强干扰
     - 裁切是否压手压脚

6. 归档终选
   - 在原目录下创建 `精修` 文件夹。
   - 只复制终选片，不移动原片。
   - 输出最终张数，并说明关键取舍。

## 挑片核心标准

详细标准见 `references/selection-rubric.md`。默认优先级如下：

- **第一优先**：真实情绪、亲密互动、幸福感
- **第二优先**：清晰度、曝光、肤色和主体识别
- **第三优先**：构图、层次、背景干净程度
- **第四优先**：纪念性、场景代表性、故事完整度

不要只挑“看镜头”的标准照。玩耍、牵手、对望、奔跑、吃东西、探索环境，这些往往更有价值。

## 安全规则

- 不做任何删除操作。
- 不用覆盖式整理，不批量重命名原片，除非用户明确要求。
- 如果 `精修` 已存在，保留原有内容；新增复制时报告重名或已存在情况，不清空目录。
- 对不确定的关键竞争帧，宁可多看原图，也不要凭缩略图草率淘汰。

## 输出预期

- 默认产出：
  - `精修` 文件夹
  - 第一轮或第二轮联络表
  - 明确的终选名单
  - 简短的审美说明与关键取舍依据

## Resources in this skill

- `scripts/contact_sheet.jxa` - macOS 原生联络表后端
- `scripts/contact_sheet_pillow.py` - Linux / Windows / macOS 通用的 Pillow 后端
- `scripts/make_contact_sheets.sh` - Bash 包装器，会自动选择 macOS 或 Python 后端
- `scripts/make_contact_sheets.ps1` - Windows PowerShell 包装器
- `references/selection-rubric.md` - 挑片标准与取舍规则
