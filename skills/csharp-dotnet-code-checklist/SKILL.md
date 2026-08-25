---
name: csharp-dotnet-code-checklist
description: Apply C#, ASP.NET Core, EF Core, and .NET-specific review rules to an existing code change. Use for C#/.NET PR or diff review, C# 代码审查, or checking an ASP.NET Core change. Do not use for non-.NET code, implementation, or architecture design without an existing change.
---

# C# / .NET Code Checklist

Review `C#`, `ASP.NET Core`, and `.NET` changes like a pragmatic senior engineer. Default to diff review, not full-repo style commentary.

## Compatibility

Best when a git diff, PR patch, changed files, or file paths are available. Use this specialist with `review-code-change` when that general review skill is available: the general skill owns change scope and reporting quality, while this skill supplies .NET-specific evidence. When repo context exists, run `scripts/inspect_dotnet_repo.ts` first to collect target frameworks, nullable, analyzer, ASP.NET Core, EF Core, test, and CI signals before judging conventions.

## Workflow

1. Start from the diff, changed files, or the exact snippets the user highlighted.
2. If repo context exists, run the bundled fact collector first:

   ```powershell
   node --no-warnings --experimental-strip-types "{baseDir}\scripts\inspect_dotnet_repo.ts" --path "<repo>"
   ```

   Use that JSON to ground recommendations about target frameworks, nullable, analyzers, ASP.NET Core, EF Core, test stack, and CI.
3. Pull only the nearby context needed to verify behavior and contracts.
4. Prioritize correctness, nullability, async/cancellation, disposal/lifetimes, security, data access, and real hot-path performance.
5. Report only evidence-based findings. If context is missing, say the assumption instead of guessing.
6. Reply in the user's language.

## Strong findings

Raise issues when the change is likely to cause:

- incorrect behavior or broken invariants
- runtime failures, null bugs, race conditions, deadlocks, or disposal bugs
- security leaks or missing access control
- expensive queries or meaningful hot-path regressions
- weak logging, swallowed exceptions, or missing cancellation
- behavior changes without useful test coverage

Do not over-report formatting nits, speculative micro-optimizations, or preference-only comments.

## Output

Use this shape:

### Review summary
- Scope:
- Overall risk:
- Top themes:

### Findings
1. `[severity]` Short title
   - Where:
   - Why it matters:
   - Evidence:
   - Suggested change:

### Checks performed
- correctness / invariants
- contracts / validation
- nullability
- async / cancellation / concurrency
- disposal / lifetimes
- data access
- security
- performance
- diagnostics / tests

### Residual risks / follow-ups
- Missing context, unanswered questions, or unverified areas

Use severities `blocker`, `high`, `medium`, `minor`.

Load `references/review-dimensions.md` when the diff touches EF Core, ASP.NET Core, DI, tests, trimming/AOT, or modern C# features.
