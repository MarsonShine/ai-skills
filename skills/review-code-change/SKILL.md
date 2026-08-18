---
name: review-code-change
description: Review pull requests, patches, commits, and working-tree diffs across programming languages with evidence-based findings focused on correctness, security, lifecycle, compatibility, performance, and test strength. Use for general code review, PR review, diff review, or architecture-risk review. For C# and .NET changes, also use the more specific csharp-dotnet-code-checklist skill.
---

# Review Code Changes

Review the actual change against its repository, not against a generic style guide. A short review with one substantiated defect is better than a long list of preferences.

## Workflow

1. Establish the exact scope: live base, exact head, dirty files, and any retargeting or rebasing since the request began.
2. Read applicable repository instructions, architecture records, public contracts, and testing policy before judging the diff.
3. Inspect the changed lines plus enough callers, callees, schemas, configuration, and tests to understand the behavior.
4. Trace important paths end to end, including failures, cancellation, cleanup, concurrency, persistence, and alternate entry points.
5. Verify claims with focused tests, static checks, logs, or reproducible reasoning from the code. Do not assume a green test suite proves semantic correctness.
6. Report only actionable findings. Separate defects from optional improvements and disclose unverified areas.

Read `references/review-dimensions.md` when the change touches concurrency, durable state, permissions, public APIs, generated output, or runtime integration.

## Specialist Routing

- For C#, ASP.NET Core, EF Core, or .NET-specific review, load `../csharp-dotnet-code-checklist/SKILL.md` in addition to this skill.
- Prefer an available language, framework, security, database, or platform specialist when it provides narrower rules.
- Keep this skill responsible for cross-cutting review quality and reporting.

## Reporting

Lead with findings ordered by impact. For each finding, state the location, defect, consequence, evidence, and smallest credible correction. If no findings survive verification, say so and list residual risks or checks you could not perform.

Do not report style nits already enforced by a passing formatter or linter unless they conceal a behavioral problem.
