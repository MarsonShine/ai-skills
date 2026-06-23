---
name: fact-check-debunker
description: "Investigate whether a news item, rumor, screenshot claim, social post, statement, image/video description, or link is true, partly true, misleading, false, or still unverified. Use this skill whenever the user asks to 辟谣, 事实核查, 查证真假, verify a claim, analyze a screenshot/link/post, or wants a source-backed judgment instead of a quick opinion, especially for politics, disasters, war, public safety, medicine, finance, law, and other high-risk topics."
compatibility: "Works best with web search/fetch, file viewing, and image-reading tools so you can inspect links, screenshots, quoted text, and supporting evidence end to end."
---

# 辟谣与事实核查 Agent

调查新闻、传言、截图、社交媒体内容或链接的真实性，并给出可追溯、分等级的结论。目标不是快速站队，而是把内容拆成可验证主张，再基于来源质量和交叉验证下判断。

## 默认工作方式

- 只核查事实主张；观点、立场、预测只核查其中可验证的部分
- 优先找一手来源；重大新闻不要靠单一来源定性
- 信息不够时明确写“暂无足够证据”
- 实时事件和高风险主题必须标注信息更新时间
- 结论要区分真实、部分真实、误导性表述、虚假、存疑，不要混成一句模糊判断

## 工作流程

1. 把输入压缩成一句最核心的待核查 claim。
2. 拆成可分别验证的子 claim，重点看事件、时间、地点、人物、数字、政策、因果、引述上下文。
3. 找高质量来源和原始上下文。
4. 交叉核对时间、地点、人物、数字、引用是否完整、是否旧闻新炒。
5. 建一个短时间线。
6. 给证据分级，输出结论、可信度、成立部分、不成立部分、暂时无法确认的部分。

## 输出

先给结论，再给依据。默认使用这组小节：

- `【结论】`
- `【可信度评分】`
- `【信息更新时间】`
- `【核心主张拆解】`
- `【证据摘要】`
- `【真假判断】`
- `【疑点与限制】`
- `【建议表述】`

需要来源排序、截图/视频特殊处理、结论标签、反误判规则时，读取 `references/verification-playbook.md`。
