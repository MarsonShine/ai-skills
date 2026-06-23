# Verification playbook

## Evidence order

Prefer sources in this order:

1. Official releases from governments, regulators, courts, police, fire, health authorities, etc.
2. Formal announcements from the company, school, hospital, institution, or organization involved
3. Authoritative international organizations such as WHO, UN, IMF, World Bank
4. Primary research papers, datasets, filings, legal texts, judgments, or statistical bulletins
5. Full video, full interview, raw livestream replay, original post

If primary sources are missing, use reliable secondary reporting that still points back to origin, timestamp, and context.

## Cross-check rules

Use at least 2-3 genuinely independent sources for major claims. Check:

- time
- place
- person / organization
- numbers
- whether the claim was reworded or sensationalized
- whether context was cut away
- whether an opinion was repackaged as fact
- whether the content is satire, parody, impersonation, fake screenshots, or AI-generated material

If multiple sources all point back to the same original post or same media outlet, treat them as one source.

## Timeline checks

Build a short timeline with:

1. when the claim first appeared
2. when the original source was published
3. when key institutions responded
4. when corrections, clarifications, updated casualty numbers, or revised policies appeared

Watch for:

- old news recycled as new
- old images or videos used as if they were current
- old policies described as "just released"
- early incomplete reporting framed as the final answer

## Evidence grades

- **A**: official documents, raw data, primary statements, full video, legal text, primary research
- **B**: reliable media, professional institution reports, named expert analysis
- **C**: ordinary media rewrites, verified social accounts, second-hand summaries
- **D**: anonymous leaks, screenshots, short clips, unattributed reposts, chat logs

Rules:

- never call something "true" on D-grade evidence alone
- for public safety, medicine, finance, law, politics, disasters, or war, the conclusion should mostly rest on A/B evidence
- if only weak evidence exists, default to `存疑` or `暂无足够证据`

## Special cases

### Screenshots, images, video descriptions

- do not treat the screenshot itself as enough
- try to find the original post, full clip, or full context
- note cropping, missing account names, missing timestamps, or platform UI mismatches
- if origin cannot be verified, say so in `疑点与限制`

### Quotes, interviews, statements

- find the full interview, full video, transcript, or broader context when possible
- do not infer a speaker's full position from one clipped sentence
- when the issue is selective quoting, prefer `误导性表述` over `虚假`

### Numbers, policy, law, medicine, finance

- prefer original filings, data tables, regulations, notices, research, or regulatory materials
- verify units, methodology, time range, and sample scope
- keep a higher evidence bar for medical and financial claims

### Real-time news

- always mark the information update time
- conditional phrasing is fine, such as “截至目前” or “现有公开证据显示”
- do not turn “not yet confirmed” into “definitely false”

## Verdict labels

- **真实**: core claims supported by multiple high-quality sources with no major contradiction
- **基本真实**: main facts hold, but some details remain lightly uncertain
- **部分真实**: some parts hold, but key numbers, causality, background, or detail are wrong or missing
- **存疑**: evidence is thin or conflicting
- **误导性表述**: not fully invented, but missing context, clipped, recycled, or exaggerated
- **虚假**: the core claim is disproven by reliable evidence, or the content is clearly fabricated
- **暂无足够证据**: current public evidence is not strong enough for a stable conclusion

## Output skeleton

```text
【结论】
<真实 / 基本真实 / 部分真实 / 存疑 / 误导性表述 / 虚假 / 暂无足够证据>

【可信度评分】
<0-100>

【信息更新时间】
<YYYY-MM-DD HH:mm TZ>

【核心主张拆解】
1. ...
2. ...

【证据摘要】
1. 来源名称
   - 支持/反驳了什么：
   - 证据等级：A/B/C/D
   - 时间：

【真假判断】
- 哪些部分成立：
- 哪些部分不准确或有误导：
- 哪些部分暂时无法确认：

【疑点与限制】
- ...

【建议表述】
- 是否建议转发
- 更准确的转述
```
