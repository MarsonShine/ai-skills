# Verification Strategy Results — 2026-10-13

The six affected skills passed frontmatter and local-reference checks. Changed Markdown and diffs passed structural checks. Plugin manifest and local marketplace structure were checked directly because the former bundled plugin-validator helper is absent on this host.

Twenty initial tool-enabled runs covered ten cases with baseline and candidate instructions in fresh contexts. Nineteen completed; the initial candidate UI run timed out after repeated browser-tool recovery. Its failure remains in [results.json](results.json). A narrow recovery rule was added, followed by one clean UI rerun, which completed with real Edge measurements and cleanup. No further behavior runs were performed after the user's request to limit evaluation effort.

| Case | Observed result |
|---|---|
| UI spacing | Baseline rendered correctly. Initial candidate produced identical HTML but over-expanded tool recovery and timed out. Follow-up candidate verified real 320/800px iframe layouts, then removed its temporary files. |
| Covered business bug | Both reused existing failing/passing tests and fixed the shared owner; independent checks passed. No new test files. |
| iOS lifecycle | Both preserved ownership, stop/restart and cleanup in source; no Xcode or iOS runtime validation. |
| CEF3 compatibility | Both passed Node behavior and old-fail/new-pass ES5 parsing checks; target CEF runtime was unavailable. Baseline's additional boundary assertions were useful, not waste. |
| Shared interface | Both preserved external sink behavior, escaping and input ownership; independent checks passed. |
| Authorization and persistence | Both retained denial regression tests; independent SQLite checks confirmed allowed writes and unchanged state on denial. |
| Explicit TDD | Both actually ran failing tests before implementation, then passed. Independent integer-format checks passed. |
| Pre-push reuse | Both verified hashes, workspace and interpreter, reused prior passing results and did not rerun the gate. |
| Code review | Both found lost output through the injected sink and explained the existing assertion gap. |
| Small business plan | Both produced relevant acceptance scenarios. Candidate explicitly distinguished recommendations from executed checks and avoided a separate test framework. |

The authorization starter test originally left SQLite connections open on Windows; both arms repaired cleanup while adding denial coverage. The reusable fixture has since been corrected and checked against the generated candidate without changing either original run.

The follow-up UI evidence covers Edge iframe geometry and DOM events, not a browser matrix or backend POST. The recovery-only refinement reuses evidence for unchanged successful paths; it was not followed by another full matrix. Source-repository AGENTS.md was reviewed separately, not injected as a global plugin instruction. Slice and .NET-specific guidance received structural and contract review, not separate full behavioral runs.

These bounded observations do not establish general time or token savings. The baseline already made reasonable testing decisions in many cases. Runtime and token telemetry are observations only; raw traces remain locally under ignored outputs/. The evaluation itself was larger than warranted for this instruction change and is not a default gate for future edits.

Plugin 0.2.0+codex.20261013120707 was reinstalled successfully. All 14 entrypoint/reference Markdown files for the six affected skills match the installed cache. No additional fresh-session model probe was run after the user requested limiting evaluation effort.
