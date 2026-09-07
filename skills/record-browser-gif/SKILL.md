---
name: record-browser-gif
description: "Record a browser workflow as a verified animated GIF for demos or PR evidence. Not for static screenshots, general video editing, or publication without a request."
---

# Record Browser GIF

Produce a truthful UI demonstration from one coherent run. Keep local recording separate from remote publication.

## Establish the Evidence

1. Identify the exact repository tree or commit, application origin, build or development mode, backend or transport, and whether the scenario uses real services, fixtures, or mocks.
2. Read repository run instructions and start the application from the requested tree with isolated scratch state when practical.
3. Preserve requested conditions. If a real service, account, credential, or backend is unavailable, report the limitation instead of silently substituting a fixture.
4. Never display or log credential values, private data, unrelated tabs, or notifications.

## Capture Semantic States

Use the available browser-control capability or the repository's existing browser automation. Do not install another browser driver without authorization.

1. Plan three to six states that tell one story: initial, input, running, result, and relevant detail.
2. Keep viewport, crop, theme, and zoom stable.
3. Wait for a concrete UI predicate before each frame: exact text, unique label, enabled control, changed title, stable status, or a specific DOM attribute. A fixed delay alone is not evidence.
4. Match completion against a unique result element, not a body-wide substring that the user's own input could satisfy.
5. Show identity, state, and outcome when demonstrating a tool call, rejection, or recovery.
6. Store lexically named screenshots in an ignored or temporary directory, such as `00-initial.png`, `01-running.png`, and `02-complete.png`.

Treat one storyboard as one run. If capture fails, restart from fresh state rather than combining frames from unrelated attempts.

## Encode

Require Python, `ffmpeg`, and `ffprobe`. Do not install missing media tools without permission.

```powershell
python "{baseDir}/scripts/encode_gif.py" `
  "<frames-directory>" `
  "<output.gif>" `
  --durations "1.5,1.5,3.5" `
  --fps 10 `
  --max-width 1200 `
  --colors 128
```

One duration applies to all source frames; otherwise provide one duration per frame. Hold the final state longest. Reduce width before colors or frame rate when the file is too large.

## Verify and Report

1. Check the encoder's JSON summary for source frames, encoded frames, dimensions, duration, and bytes.
2. Inspect the encoded GIF itself. Confirm order, legibility, final-state hold, crop consistency, and absence of sensitive content.
3. Confirm frames and output exist only in intended scratch or deliverable paths.
4. Return the GIF path and provenance: commit or tree, origin, run mode, backend, and real versus fixture data.

Stop after local delivery unless the user explicitly asks to attach or publish it. For remote publication, read `references/publishing.md` and follow the repository's asset policy.
