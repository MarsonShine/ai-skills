# WeChat draft assistant acceptance

2026-11-11, Windows. Base `afb1f6c` with the new [skill](../../skills/wechat-mp-publisher/SKILL.md). Node 26.8.2, Python 3.12, Pillow 12.3.0. The Node entrypoint uses built-in TypeScript support, fetch and SQLite. Python prepares local images and reads optional YAML profiles.

## Local evidence

- The preview checks cover revision identity, tampering, concurrent generation, text fidelity and all four layouts. Edge loaded the prepared images at 375 and 430 pixels without horizontal overflow. Changing scene, cover and image order exported a layout for a new preview.
- The CLI integration check revises Chinese copy and image order, rejects the superseded version, then sends the confirmed bytes through the real adapter with a simulated WeChat response. Image cases cover EXIF rotation and location stripping, strict pixel equality and separate body and cover size limits.
- The simulated draft cases cover duplicate requests, missing permissions, ambiguous creation, claim, process death, failed readback, human edits and stale approvals. A separate first-use pass created an offline travel preview with the second photo as cover. A simulated revision change during submission exposed stale uploads; regression checks now require the current revision before every new upload and immediately before writing the draft.
- A fresh Codex CLI routing pass received the 26 descriptions and 52 prompts without expected answers. All selections matched, including the photo-to-draft request and the family-diary editing near miss. This was a catalog-level evaluation.
- On the final implementation, 21 Node checks and four Python image tests passed, along with strict TypeScript checking. A new Codex session discovered `ai-skills:wechat-mp-publisher` at installed version `0.2.0+codex.20261111103201`, and that copy generated the sample travel preview.
- The installed package passed the catalog, frontmatter and clean-package checks. At the time of validation, the shared checkout's full-tree checks also saw an unrelated in-progress `workbuddy-wechat-article` entry and its Python cache. The install snapshot excludes that work.

Run from the repository root with `python -m pip install -r skills/wechat-mp-publisher/requirements.txt`, then `python -B scripts/test_wechat_images.py` and `node --test scripts/test_wechat_*.mjs`. The package and catalog checks are in the [development guide](../../docs/skill-development-guide.md).

## Awaiting the target account

No credentials were configured for this run. The WeChat account's actual draft and permanent-cover rights, remote image results and phone render remain unverified. Follow the [single-draft acceptance procedure](../../skills/wechat-mp-publisher/references/wechat.md) after the author selects an account and confirms the test preview. Author-specific voice tuning needs examples and editorial decisions from the author.
