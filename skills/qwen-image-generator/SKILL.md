---
name: qwen-image-generator
description: "Generate and save images when the user explicitly chooses Qwen, DashScope, or this Qwen image workflow. Not for provider-neutral generation, image editing, or ID photos."
---

# Qwen Image Generator

Turn rough image requests into saved local files. Default to doing the work end to end: load preferences, ask only for still-missing settings, write one concrete English prompt, generate sequentially, save immediately, and report the file paths plus the final prompt used.

## Compatibility

Works best with PowerShell, Node.js 22+, environment variables, and file tools. The PowerShell entry is thin; `scripts/generate_qwen_image.ts` owns the DashScope call, polling, downloads, and JSON output.

## Runtime layout

| File | Role |
| --- | --- |
| `scripts/generate_qwen_image.ps1` | Windows entrypoint |
| `scripts/generate_qwen_image.ts` | DashScope client, polling, downloads, JSON output |
| `references/config/extend-schema.md` | `EXTEND.md` keys |
| `references/config/first-time-setup.md` | optional saved-preference setup |
| `references/prompting.md` | style presets, prompt shaping, flashcard rules |

## Credentials

Resolve credentials in this order:

1. `QWEN_IMAGE_API_KEY`
2. `DASHSCOPE_API_KEY`

Optional: `DASHSCOPE_BASE_URL`

If no key exists, prepare the prompt and effective settings, report the missing credential, and ask the user to configure it locally. Do not submit generation or claim success until a key is available.

## Preferences

Check for `EXTEND.md` in this order:

1. `.baoyu-skills/qwen-image-generator/EXTEND.md`
2. `$XDG_CONFIG_HOME/baoyu-skills/qwen-image-generator/EXTEND.md`
3. `$HOME/.baoyu-skills/qwen-image-generator/EXTEND.md`

If none exists, use the built-in defaults below and continue. Read `references/config/first-time-setup.md` only when the user wants to save or change persistent defaults; an image request does not require a preference file.

Built-in defaults when neither the request nor `EXTEND.md` overrides them:

- model: `qwen-image-2.0`
- style: `flat-illustration`
- size: `1024x1024`
- text policy: `avoid`
- prompt enhancement: `true`
- watermark: `false`
- output directory: `./generated-images/`

## Working rules

1. Parse the request for subject, style, size, visible text, and output path.
2. Fill missing values from `EXTEND.md`, then built-in defaults. Explicit request values take precedence.
3. Ask only for still-missing values that materially change the result.
4. Write the final prompt in English.
5. Prefer project batch wrappers when they already handle reruns or selective regeneration. Otherwise run `scripts/generate_qwen_image.ps1`.
6. Generate sequentially by default. Only parallelize when the user explicitly asks.
7. Save each successful result immediately and report the saved path, final prompt, and effective settings.

Load `references/prompting.md` when the request needs preset choice, educational-image rules, or prompt-shaping guidance.
