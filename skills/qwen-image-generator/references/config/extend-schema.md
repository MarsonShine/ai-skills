# EXTEND Schema

`EXTEND.md` is a small YAML file used by `qwen-image-generator` to hold user or project defaults.

## Supported Keys

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `model` | string | `qwen-image-2.0` | DashScope image model |
| `default_style` | string | `flat-illustration` | Default style preset or custom style description |
| `default_size` | string | `1024x1024` | Default image size |
| `render_text` | string | `avoid` | `avoid` or `allow-short` |
| `prompt_extend` | boolean | `true` | Whether DashScope prompt enhancement should be enabled |
| `watermark` | boolean | `false` | Whether generated images should include the DashScope watermark |
| `default_output_dir` | string | `./generated-images/` | Default output directory for generated files |

## Example

```yaml
model: qwen-image-2.0
default_style: clean-educational
default_size: 1792x1024
render_text: avoid
prompt_extend: true
watermark: false
default_output_dir: ./generated-images/
```

## Resolution Rules

1. Explicit user request wins
2. `EXTEND.md` wins over built-in defaults
3. If a required parameter is still missing, ask the user only for that missing field
