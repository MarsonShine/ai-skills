# Current State

Updated: 2026-11-11
Branch: main
Baseline: afb1f6c plus the WeChat draft assistant
Status: awaiting account acceptance
Task: [WeChat draft assistant](workspaces/wechat-mp-publisher/README.md)
Next: After the author configures credentials and confirms the account and sample, verify one real draft, update it and check the four layouts in WeChat.

## Current Work

- Maintain one current-state entry here; read only the task and module material needed next.
- The Codex skill, offline previews and simulated draft recovery are implemented. Current evidence and outstanding account checks are in the linked task.
- The earlier harness recovery pilot is complete: [evidence](workspaces/harness-evidence-pilot/README.md).
- Install versions and host-specific drift have one owner: [install state](docs/install-state.md).

## Verification

- Local draft workflow checks and the catalog routing evaluation are recorded in the [acceptance result](workspaces/wechat-mp-publisher/README.md).
- Baseline `26d1c79`: [skills CI passed](https://github.com/MarsonShine/ai-skills/actions/runs/39720607992).
- Local closeout regression, support-document regression, package checks, skill checks and image-tool smoke passed; exact scope is recorded in the completed task. CI status must be read from GitHub for the requested revision; earlier success is not transferred.
- The unavailable plugin-validator helper is not reported as a pass; catalog, skill and behavioral checks remain available.

## Navigation

- [Cross-session workflow](docs/multi-session-workflow.md)
- [Decisions](docs/decisions/README.md)
- [Historical evidence index](workspaces/README.md) — open only when the task requires it.
