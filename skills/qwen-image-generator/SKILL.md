---
name: qwen-image-generator
description: Generate images with DashScope Qwen-Image 2.0 from rough user requests and save them locally. Use this whenever the user asks to generate an image, illustration, poster, flashcard, teaching card, cover art, scene image, mascot, product concept, or "文生图"/"画一张图", even if the request is vague. Supports first-time setup via EXTEND.md, fills missing style and size from saved preferences, and asks only for still-missing image parameters.
compatibility: "Works best with PowerShell, environment variables, and file tools. Uses a bundled PowerShell script to call DashScope Qwen-Image 2.0 and download the generated image files."
---

# Qwen Image Generator

Turn rough image ideas into concrete Qwen-Image generations. Default to doing the work end-to-end: load preferences, ask only for still-missing parameters, build a strong prompt, generate the image, save it locally, and report the saved path and prompt used.

## Script Directory

Scripts live in `scripts/`. Treat `{baseDir}` as the directory containing this `SKILL.md`.

| Script | Purpose |
|--------|---------|
| `scripts/generate_qwen_image.ps1` | Calls DashScope Qwen-Image 2.0 synchronously, downloads image files, and prints a JSON summary |

## Environment Variables

Before generation, resolve credentials in this order:

1. `QWEN_IMAGE_API_KEY`
2. `DASHSCOPE_API_KEY`

Optional:

- `DASHSCOPE_BASE_URL` - override the default DashScope API root

If no API key is present, stop and tell the user to set one of the supported environment variables. Do not pretend generation succeeded.

## Preferences (EXTEND.md)

Check `EXTEND.md` in this order:

```powershell
if (Test-Path .agent-skills/qwen-image-generator/EXTEND.md) { "project" }
$xdg = if ($env:XDG_CONFIG_HOME) { $env:XDG_CONFIG_HOME } else { "$HOME/.config" }
if (Test-Path "$xdg/agent-skills/qwen-image-generator/EXTEND.md") { "xdg" }
if (Test-Path "$HOME/.agent-skills/qwen-image-generator/EXTEND.md") { "user" }
```

| Path | Location |
|------|----------|
| `.agent-skills/qwen-image-generator/EXTEND.md` | Project directory |
| `$HOME/.agent-skills/qwen-image-generator/EXTEND.md` | User home |

| Result | Action |
|--------|--------|
| Found | Read it, apply preferences, and briefly note which path is in use on first use in the session |
| Not found | Run the blocking first-time setup before generating any image |

Supported keys and template: [references/config/extend-schema.md](references/config/extend-schema.md)

### First-Time Setup (BLOCKING)

When `EXTEND.md` is not found, do not jump into prompt writing or image generation. Run first-time setup first.

Full flow: [references/config/first-time-setup.md](references/config/first-time-setup.md)

Ask in the user's language. Collect these preferences:

1. Default visual style
2. Default image size
3. Default text policy
4. Whether prompt enhancement should be on by default
5. Default output directory
6. Where to save the preferences

After setup, create `EXTEND.md`, confirm the path, then continue the image task.

## Defaults

Use these defaults when neither the request nor `EXTEND.md` overrides them:

| Setting | Default | EXTEND.md key | Meaning |
|---------|---------|---------------|---------|
| Model | `qwen-image-2.0` | `model` | DashScope image model |
| Style | `flat-illustration` | `default_style` | Default visual treatment |
| Size | `1024x1024` | `default_size` | Output resolution |
| Text policy | `avoid` | `render_text` | Whether to avoid rendered text inside the image |
| Prompt enhancement | `true` | `prompt_extend` | Whether DashScope should expand the prompt |
| Watermark | `false` | `watermark` | Whether DashScope watermark should be enabled |
| Output directory | `./generated-images/` | `default_output_dir` | Where generated images should be saved |

## Style Presets

The user can provide any custom style description. If they do not, prefer one of these presets:

| Preset | Meaning |
|--------|---------|
| `flat-illustration` | Clean flat-color illustration, simple composition, modern editorial clarity |
| `clean-educational` | Minimal textbook or flashcard look, centered subject, uncluttered background |
| `anime` | Soft anime-inspired illustration without excessive decorative detail unless requested |
| `3d-cartoon` | Friendly stylized 3D character or object rendering |
| `photorealistic` | Realistic photo-like scene or product image |
| `watercolor` | Painted watercolor look with soft textures |

## Workflow

Follow this sequence:

1. Load preferences from `EXTEND.md`, or run first-time setup if none exists.
2. Parse the request for explicit parameters:
   - subject or scene
   - style
   - size
   - visible text requirements
   - output location or filename
3. Fill missing parameters from `EXTEND.md`.
4. Ask only for parameters that are still unresolved.
5. Build a concrete final prompt in English.
6. Run `scripts/generate_qwen_image.ps1`.
7. If multiple images or a word list are requested, generate them **sequentially by default**. Do not parallelize unless the user explicitly asks for concurrency.
8. Save each successful result immediately and return the file path, prompt, and key generation settings.

## Batch Generation Defaults

When the task requires multiple images:

- default to **sequential generation**, one request at a time
- do **not** start parallel generations unless the user explicitly asks for concurrent generation
- save each image immediately after it is generated
- on rerun, **skip outputs that already exist** and continue from the next missing item
- if one item fails, record the failure, continue with the remaining items when possible, and summarize failures clearly at the end
- for rate-limit errors, use retry with backoff instead of restarting the whole batch

## Missing-Information Rules

- Never ask for style if the user already gave one.
- Never ask for size if the user already gave one.
- Never ask for values already available in `EXTEND.md`.
- If a request is still usable without extra clarification, proceed.
- Ask follow-up questions only for details that materially change the result, typically style, size, text policy, or output location.
- Ask in the smallest possible set. Do not ask the user to re-state the whole prompt.

## Prompt-Building Strategy

Build prompts in two passes.

### Pass 1: Extract scene semantics

Figure out these fields from the request:

- `mainSubject` - the main object, person, creature, or focal concept
- `supportingVisual` - one optional helper element if it truly clarifies the idea
- `actionOrGesture` - the visible action, pose, or interaction
- `sceneSetting` - minimal setting only when needed
- `backgroundHint` - plain or lightly directed background guidance
- `overlayText` - exact visible text only when the user explicitly wants it
- `negativeElements` - things that should not appear

Keep each field short and concrete. Do not over-design the scene.

### Pass 2: Write the final image prompt

- Write the final prompt in English, even if the user asked in Chinese.
- Keep it model-agnostic in wording, but use settings compatible with the current Qwen-Image 2.0 DashScope API through the script.
- Prefer clear nouns, visible actions, composition guidance, and concise style language.
- Avoid vague filler such as "high quality masterpiece" unless the user explicitly wants that aesthetic.
- If `render_text` is `avoid`, do not ask the model to render long text. Instead, reserve a clean blank area for later manual overlay when text matters.
- Add a short negative clause only when it prevents likely failure modes.

## Educational and Flashcard Requests

This skill should reuse the same design intent as the educational flashcard prompt builder pattern:

- favor semantic clarity over beauty
- keep the subject large, centered, and easy to understand
- keep the background plain or minimally directed
- avoid decorative clutter, glamour portrait styling, and scenic filler
- avoid unnecessary visible text
- use only the minimum props needed to teach the concept

Apply these rules whenever the request is for:

- alphabet cards
- vocabulary cards
- phrase meaning scenes
- textbook illustrations
- classroom teaching images
- children's English-learning visuals

For alphabet cards:

- show only the exact requested letter if visible text is required
- pair it with one simple matching object

For word or phrase cards:

- prefer text-free illustrations
- if the user needs text shown, keep it exact and very short
- reserve clean space rather than forcing long text rendering

## Size Guidance

Use the user's requested size when available. Otherwise use the configured default. Common values:

| Size | Best for |
|------|----------|
| `1024x1024` | Square illustrations, icons, stickers, object studies |
| `1024x1792` | Posters, book covers, mobile wallpapers, portrait scenes |
| `1792x1024` | Flashcards, banners, wide teaching scenes, landscape compositions |

## Output Path Rules

If the user gave an output path or filename, use it.

Otherwise:

1. Start from `default_output_dir` in `EXTEND.md`, or `./generated-images/`
2. Create a short slug from the request subject
3. Save as `{output_dir}/{slug}-{timestamp}.png`

If multiple images are requested, save them as `-01`, `-02`, and so on.

## Execution

Run the bundled script from PowerShell. Example:

```powershell
powershell -ExecutionPolicy Bypass -File "{baseDir}\scripts\generate_qwen_image.ps1" `
  -Prompt "<final english prompt>" `
  -Size "1024x1024" `
  -OutputPath ".\generated-images\apple-card.png" `
  -PromptExtend:$true `
  -Watermark:$false
```

The script prints JSON with:

- `model`
- `size`
- `taskId`
- `imageUrls`
- `savedFiles`

Read that JSON and report the saved file path succinctly.

## Output Expectations

After generation, report:

1. The saved file path or paths
2. The final prompt actually used
3. The effective style, size, and text policy

If generation fails, surface the API or credential problem clearly. Do not hide it behind a generic success message. For batch jobs, report which items succeeded, which were skipped, and which failed.

## Example Requests

- "帮我画一张单词 apple 的英语教学闪卡，风格可爱一点"
- "Generate a clean mascot illustration for a study app, blue and white, square image"
- "做一张横版海报图，主题是 AI learning community，先别放字"

## Resources

- `references/config/first-time-setup.md` - first-use preference flow
- `references/config/extend-schema.md` - supported configuration keys and template
- `scripts/generate_qwen_image.ps1` - deterministic DashScope generation helper
