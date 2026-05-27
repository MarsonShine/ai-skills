---
name: first-time-setup
description: First-time setup flow for qwen-image-generator preferences
---

# First-Time Setup

When no `EXTEND.md` exists, collect image-generation defaults before any generation work starts.

## Blocking Rule

Do not:

- start prompt writing
- run the image script
- ask unrelated follow-up questions

Only complete setup, save `EXTEND.md`, then continue the user's image task.

## Questions

Ask in the user's language.

### Question 1: Default Visual Style

```yaml
header: "Style"
question: "What should the default image style be?"
options:
  - label: "Flat illustration (Recommended)"
    description: "Clean, versatile, easy to control"
  - label: "Clean educational"
    description: "Minimal textbook or flashcard style"
  - label: "Anime"
    description: "Stylized anime-inspired illustration"
  - label: "3D cartoon"
    description: "Friendly stylized 3D rendering"
  - label: "Photorealistic"
    description: "Realistic, photo-like image"
  - label: "Watercolor"
    description: "Soft painted look"
```

Users may also type a custom style.

### Question 2: Default Image Size

```yaml
header: "Size"
question: "What default image size should be used?"
options:
  - label: "1024x1024 (Recommended)"
    description: "Square image"
  - label: "1024x1792"
    description: "Portrait image"
  - label: "1792x1024"
    description: "Landscape image"
```

### Question 3: Text Policy

```yaml
header: "Text"
question: "How should text inside generated images be handled by default?"
options:
  - label: "Avoid rendered text (Recommended)"
    description: "Prefer text-free images or clean blank space for later overlay"
  - label: "Allow short exact text"
    description: "Permit very short visible text when the user requests it"
```

### Question 4: Prompt Enhancement

```yaml
header: "Prompt"
question: "Should DashScope prompt enhancement be enabled by default?"
options:
  - label: "Yes (Recommended)"
    description: "Let DashScope expand short prompts"
  - label: "No"
    description: "Use only the prompt as written"
```

### Question 5: Default Output Directory

```yaml
header: "Output"
question: "Where should generated images be saved by default?"
options:
  - label: "generated-images (Recommended)"
    description: "Save to ./generated-images/"
```

Users may type a custom directory path.

### Question 6: Save Location

```yaml
header: "Save"
question: "Where should these preferences be saved?"
options:
  - label: "User (Recommended)"
    description: "$HOME/.agent-skills/ (all projects)"
  - label: "Project"
    description: ".agent-skills/ (current project only)"
```

## Save Locations

| Choice | Path | Scope |
|--------|------|-------|
| User | `$HOME/.agent-skills/qwen-image-generator/EXTEND.md` | All projects |
| Project | `.agent-skills/qwen-image-generator/EXTEND.md` | Current project |

## EXTEND.md Template

```yaml
model: qwen-image-2.0
default_style: flat-illustration
default_size: 1024x1024
render_text: avoid
prompt_extend: true
watermark: false
default_output_dir: ./generated-images/
```

## After Setup

1. Create the chosen directory if needed
2. Write `EXTEND.md`
3. Confirm: `Preferences saved to [path]`
4. Continue the pending image-generation task using the saved defaults
