# Session Closeout Implementation

Task: T-20261022-CLEAN-STATE
Status: in_progress
Baseline: ai-skills `26d1c79`; MS.Microservice `b6d581a`.
Request: implement all five clean-state slices, validate, commit per slice and push both repositories.

## Contract

Keep current state accurate and bounded, preserve useful historical evidence, add read-only checks, remove packaged environments only after establishing reconstruction, and demonstrate resumption from repository files.

Out of scope: .NET business changes, dependency-security remediation, new tracing infrastructure, automatic cleanup schedules and automatic harness adoption in this source repository.

| Slice | Proposed commit | Acceptance | State |
| --- | --- | --- | --- |
| 1 | docs: correct current state and retire completed task | Relative links resolve; current facts match Git/CI; previous task remains accessible | passed |
| 2 | docs: define state and evidence lifecycle | Single owners; input-based freshness; bounded startup and archive rules | pending |
| 3 | feat(harness): check session closeout without writes | Regression fixtures for conflicts, links, scope and scratch; read-only repeatability | pending |
| 4 | chore(skills): remove packaged Python environments | Clean dependency reconstruction; representative image-tool smoke; no tracked runtime caches | pending |
| 5 | test: verify repository resumption and refresh installation | Two repository exercises, installation hashes, current-state handoff and push | pending |

## Baseline Observations

- ai-skills PROGRESS.md still described the pre-install version and already-finished push/pilot work.
- MS active.md retained the completed recovery task; its contract will live beside its existing evidence.
- 3,058 tracked skill files include 2,941 virtual-environment files across id-photo-maker and photo-selector, plus seven standalone bytecode files. Counts overlap with bytecode inside the environments.
- Both workflow documents treated later commits as automatic evidence invalidation, regardless of affected inputs.
- The old .codex-tmp/finalize-ms-pilot.py is a known disposable artifact from the previous session; other ignored files have not been classified.
- Baseline ai-skills CI passed. MS dotnet-ci run 39720615089 failed at Test before these edits; another workflow succeeded. This task does not relabel the .NET failure as a pass.

## Evidence

Record each slice's checks here; retain task-specific durable evidence, not a transcript of every command. No model-quality or token-savings claim follows from structural checks.

Slice 1: relative links passed; previous task preserved; Git/CI baseline facts inspected. No runtime code changed.
