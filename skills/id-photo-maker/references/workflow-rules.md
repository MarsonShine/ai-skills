# Workflow Rules

## 1. Route by input type first

### Text only

- Collect `size`, `background`, and `framing`.
- Confirm that the user really wants AI generation.
- If yes, obtain Liblib credentials.
- Translate the request into concise English before calling Liblib.
- After Liblib returns an image, process it into the final ID photo and render the print pages.

### Local photo

- Default to photo-only processing.
- Do **not** ask for AK/SK unless the user explicitly asks for Liblib generation.
- If the user asks for Liblib `img2img`, explain that Liblib requires a public image URL. Ask for that URL or offer to continue with local processing instead.

### Public image URL

- Download it locally for normal photo processing.
- Only pass it into Liblib `img2img` when the user explicitly wants generation.

## 2. Ask missing questions in this order

1. `size`
2. `background`
3. `framing`
4. `need_generation`
5. `AccessKey / SecretKey`
6. `save_credentials`

Keep the flow tight. If one answer naturally provides the next field, do not re-ask it.

## 3. Liblib prompt rules

- Keep prompts in English.
- Preserve identity and utility before style.
- Good default backbone for text2img:

```text
formal id photo, front-facing person, realistic face, centered composition, clean studio lighting, plain background, high detail, no watermark
```

- Add user-specific attributes carefully:
  - age range
  - hairstyle
  - clothing preference
  - expression
  - target background color

Avoid overloaded art prompts such as `masterpiece, best quality, 8k, ultra detailed` unless the user clearly wants that look.

## 4. Generation settings

- Prefer `aspectRatio=portrait` for most ID photo generation tasks.
- Use explicit `imageSize` only when a custom canvas is truly needed.
- Default `steps=30`.
- Default `imgCount=1` unless the user asks for multiple options.
- Use `controlnet` only when the user gives a suitable public reference image.

## 5. Photo processing rules

- Run background removal and replace with the requested solid color.
- Fit the subject into the requested framing preset.
- Export the finished photo as PNG for printing.
- Save `metadata.json` so later steps can reuse the resolved size and output paths.

## 6. Print rendering rules

- Generate static HTML using true physical units in `mm`.
- Produce print-safe pages for `A4` and `6inch` unless the user explicitly limits the output.
- Tell the user to print at `100% scale` with no browser shrink-to-fit.

## 7. Failure handling

- If Liblib credentials are missing, stop and ask the user.
- If photo dependencies are missing (`Pillow`, `rembg`), surface the exact install command.
- If the user asks for local-file `img2img` without a public URL, do not invent an upload workflow.
- If the user requests `full-body`, explain that it is a custom layout rather than a conventional ID-photo standard.
