# Prompting rules

## Style presets

Use the user's exact style when they give one. Otherwise prefer one of these:

| Preset | Meaning |
| --- | --- |
| `flat-illustration` | Clean flat-color illustration, simple composition, modern editorial clarity |
| `clean-educational` | Minimal textbook or flashcard look, centered subject, uncluttered background |
| `anime` | Soft anime-inspired illustration without extra decorative detail unless requested |
| `3d-cartoon` | Friendly stylized 3D character or object rendering |
| `photorealistic` | Realistic photo-like scene or product image |
| `watercolor` | Painted watercolor look with soft textures |

## Missing-information rules

- Never ask for style if the user already gave one.
- Never ask for size if the user already gave one.
- Never ask for values already available in `EXTEND.md`.
- If the request is still usable without more clarification, proceed.
- Ask follow-ups only for details that materially change the result, usually style, size, text policy, or output path.
- Ask in the smallest possible set. Do not make the user restate the whole prompt.

## Two-pass prompt building

### Pass 1: extract scene semantics

Pull out only the fields that matter:

- `mainSubject`
- `supportingVisual`
- `actionOrGesture`
- `sceneSetting`
- `backgroundHint`
- `overlayText`
- `negativeElements`

Keep each field short and concrete. Do not over-design the scene.

### Pass 2: write the final prompt

- Write the final prompt in English, even if the user asked in Chinese.
- Prefer clear nouns, visible actions, composition guidance, and concise style language.
- Avoid vague filler such as "high quality masterpiece" unless the user explicitly wants that aesthetic.
- If `render_text` is `avoid`, do not ask the model to render long text. Leave clean space for later overlay instead.
- Add a short negative clause only when it prevents likely failure modes.

## Educational and flashcard requests

For teaching images, optimize for clarity over beauty:

- keep the subject large, centered, and easy to understand
- keep the background plain or lightly directed
- avoid decorative clutter, glamour portrait styling, and scenic filler
- avoid unnecessary visible text
- use only the minimum props needed to teach the concept

Apply this to alphabet cards, vocabulary cards, phrase scenes, textbook illustrations, classroom images, and children's English-learning visuals.

For alphabet cards:

- show only the exact requested letter when visible text is required
- pair it with one simple matching object

For word or phrase cards:

- prefer text-free illustrations
- if text is required, keep it exact and very short
- reserve clean space instead of forcing long rendered text

## Size guidance

| Size | Best for |
| --- | --- |
| `1024x1024` | Square illustrations, icons, stickers, object studies |
| `1024x1792` | Posters, book covers, mobile wallpapers, portrait scenes |
| `1792x1024` | Flashcards, banners, wide teaching scenes, landscape compositions |

## Output path rules

If the user gives an output path or filename, use it.

Otherwise:

1. Start from `default_output_dir` in `EXTEND.md`, or `./generated-images/`
2. Create a short slug from the request subject
3. Save as `{output_dir}/{slug}-{timestamp}.png`

If multiple images are requested, append `-01`, `-02`, and so on.
