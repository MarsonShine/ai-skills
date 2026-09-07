# GPT-6 Astra 技能库审查

审查日期：2026-09-07。基线：`16f105b1f7d9789450f9a159a635ce07cebadecc`。工作分支：`GPT6-Astra`。

已审查全部 24 个技能，保留其名称和独立用途，精简全部发现描述，并调整有证据支持的流程冲突。没有足够依据删除整个技能：现有重叠主要来自相邻任务，仍可通过明确边界与按需组合区分。

## 依据与适用范围

[OpenAI 官方 Astra 指南](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)建议审查技能造成的指令冲突、提前停工和过度验证，明确用户指令优先级，并按任务调整自主执行和输出方式。

[Eric Provencher 的文章](https://x.com/pvncher/status/2095991462416490862)强调简短的发现描述、渐进加载、减少过细步骤，以及重新审视全局指令。本次使用用户提供的文章正文；X 网页请求返回 403，未将搜索摘要或二手转述当作原文。

具体改动是将上述原则应用到本仓库的判断，不代表官方逐项要求。技能保持跨模型可用；未给每个技能添加 Astra 专属提示、模型配置或强制子代理策略。仓库没有需要迁移的 OpenAI API 调用，Qwen 与 Liblib 的服务选择和脚本保持原样。

## 全量结论

以下各项均已缩短 `description`；“保留流程”表示正文未修改。

| 技能 | 处理与依据 |
| --- | --- |
| [business-solution-architect](../skills/business-solution-architect/SKILL.md) | 模板改为覆盖参考，用户格式优先；避免为填满章节增加功能。 |
| [csharp-dotnet-code-checklist](../skills/csharp-dotnet-code-checklist/SKILL.md) | 按缺失事实运行采集器，复用已知信息；与通用审查共用一份报告，删除固定长检查清单。 |
| [fact-check-debunker](../skills/fact-check-debunker/SKILL.md) | 删除默认百分制评分、固定八节输出和无条件时间线；按证据决定是否继续查证，保留重大争议的独立佐证要求。 |
| [find-code-simplifications](../skills/find-code-simplifications/SKILL.md) | 架构和决策文档按候选所需加载；保留外部消费者、动态调用与兼容性证明要求。 |
| [id-photo-maker](../skills/id-photo-maker/SKILL.md) | 入口压缩为参数、路由、命令、凭证和交付；构图使用已有 standard 默认值，合并必要追问，删除过时固定安装路径。 |
| [implement-minimal-code](../skills/implement-minimal-code/SKILL.md) | 保留流程：已有范围保护、根因修复和按风险验证，不再叠加新模型口号。 |
| [loop-orchestrator](../skills/loop-orchestrator/SKILL.md) | 保留流程：触发、停止、成本与状态是循环任务所需契约，不应因模型升级删除。 |
| [maintain-decision-records](../skills/maintain-decision-records/SKILL.md) | 保留流程：记录归属、生命周期和冻结档案规则有实际作用。 |
| [markdown-pdf-export](../skills/markdown-pdf-export/SKILL.md) | 一次导出不再默认复制永久工具链；交付检查关注页面可用性，无法视觉检查时说明。 |
| [merge-stacked-prs](../skills/merge-stacked-prs/SKILL.md) | 保留流程：栈顺序、精确 head、官方栈对象及必需检查属于远端操作契约。未重新验证 GitHub 功能可用性。 |
| [photo-selector](../skills/photo-selector/SKILL.md) | 合并重复平台命令；少量图可直接查看，按需要增加筛选轮次；仅联络表请求不自动复制照片，家庭审美不套用到所有题材。 |
| [qwen-image-generator](../skills/qwen-image-generator/SKILL.md) | 删除强制首次问卷和偏好文件写入；使用现有默认值，持久化只在用户需要时进行；缺凭证仍可先准备 prompt。 |
| [record-browser-gif](../skills/record-browser-gif/SKILL.md) | 保留流程：同一次运行、语义完成判据和成品检查保证演示真实；公开发布仍需要相应请求。 |
| [resume-builder](../skills/resume-builder/SKILL.md) | 删除重复结构、默认额外版本和数字套用；量化统一归属到来源证据规则，不再把“看起来合理”当作事实。 |
| [review-code-change](../skills/review-code-change/SKILL.md) | 限定预读到变更路径相关契约，保留缺陷证据与重要路径检查。 |
| [review-technical-prose](../skills/review-technical-prose/SKILL.md) | 保留流程：完整契约和信息归属属于专门任务，与普通润色不同。 |
| [reviewable-change-slices](../skills/reviewable-change-slices/SKILL.md) | 默认 8 文件／约 400 行改为拆分参考，不再自动触发审批；保留用户硬限制、逐片检查点和明确的多片授权。 |
| [run-pre-push-checks](../skills/run-pre-push-checks/SKILL.md) | 保留流程：已经要求选择相关检查、复用有效通过结果，不重复运行全套。 |
| [sync-bilingual-docs](../skills/sync-bilingual-docs/SKILL.md) | 保留流程：双侧独立改动的冲突和元数据更新需要明确语义归属。 |
| [sync-documentation-site](../skills/sync-documentation-site/SKILL.md) | 验证按受影响的投影和路由选择；修复参考文档中的兄弟技能相对路径。 |
| [translate-tech-en-zh](../skills/translate-tech-en-zh/SKILL.md) | 去掉 Windows Downloads 与 PowerShell 前提；明确代码语义保留和解释性注释翻译的边界，用户指定格式优先。 |
| [trim-reasoning-leakage](../skills/trim-reasoning-leakage/SKILL.md) | 去掉为已有正文规则强制加载另一个审查技能；真正需要广泛契约审查时再组合。 |
| [windows-reclaim-disk-space](../skills/windows-reclaim-disk-space/SKILL.md) | 承认已授权批次，不要求逐文件重复确认；保留精确路径、活动进程、数据损失和禁删目录规则。 |
| [write-natural-prose](../skills/write-natural-prose/SKILL.md) | 保留流程：语言证据、事实约束和示例非模板规则已经清楚，不额外加入套话黑名单。 |

## 全局指令与删减

[`AGENTS.md`](../AGENTS.md)由 196 行压缩到 62 行：合并重复的语言选择、技能结构和脚本规则，保留根因／不变量修复及回归证据要求，加入按需读取、已授权工作完成边界和有效验证复用。它管理本仓库维护，不会随某个已安装技能自动成为其他仓库的全局指令。

保留发现层的相邻任务排除条件；删除冗长的触发同义词和能力枚举。保留所有 24 个名称、UI 元数据与自动发现策略，避免破坏现有调用。没有删除脚本、模板或确定性处理能力。

| 范围 | 修改前字符数 | 修改后字符数 | 减少 |
| --- | ---: | ---: | ---: |
| 24 个技能描述 | 7,314 | 3,623 | 50.5% |
| 24 个 SKILL.md，包含描述 | 72,637 | 59,385 | 18.2% |
| AGENTS.md | 6,842 | 4,904 | 28.3% |

按统一换行后的 Unicode 字符计数；中英文混合，不能直接等同于 token、时延或费用节省。这些范围也不能相加作为每次请求的上下文节省，因为技能正文按需加载。

## 验证与局限

- 插件结构验证通过；全部 24 个技能通过 `quick_validate.py`。Windows 默认 GBK 导致首次读取失败，使用 `python -X utf8` 后通过，并更新维护指南命令。
- 检查 55 处明确的本地资源引用。发现并修复 `references/projection-checklist.md` 从参考目录跳到兄弟技能时少一层 `../` 的问题；没有修改被引用技能的位置。
- 检查现有 50 条路由用例的名称引用、预期与禁止集合一致性，并按描述人工检查任务边界；未运行独立模型的自动选技评测。
- 记录 20 条行为情境的指令契约检查，覆盖默认值、真正缺参、授权覆盖、审查组合、翻译、简历证据、导出与破坏性操作的正反情形。记录不代表模型执行通过率。
- 实测本地证件照入口默认构图与 295×413 像素输出、A4／6 寸打印文件、原图校验和；测试使用合成图并跳过自动抠图。挑片包装器显式指定 Windows Python 后通过，.NET 采集器自检通过。
- 挑片首次运行选中了已有的非 Windows `.venv/bin/python`；使用现有 `PHOTO_SELECTOR_PYTHON` 覆盖解决本次验证，未修改包装器。没有测试真实照片审美、抠图、付费生图或 PDF 页面渲染。

详见 [`workspaces/gpt6-astra-audit`](../workspaces/gpt6-astra-audit/README.md)。本次结果是有依据的指令精简与静态／局部命令验证；没有 Astra 前后对照任务数据，不能宣称已证明质量、成本或选技准确率提升。

采用该版本时，按[维护指南](skill-development-guide.md)重新安装并开启新任务，才会加载新描述。安装成功不等同于模型行为评测通过。下一次有真实任务数据时，应优先比较不必要追问、提前结束、选技误触发和验证成本，而非继续按字数删规则。
