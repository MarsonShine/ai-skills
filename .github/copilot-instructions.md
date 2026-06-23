# Copilot Instructions

This repository uses `AGENTS.md` as the canonical agent instruction file.

Follow the language selection rules in `AGENTS.md`:

- Markdown for skill judgment and workflow instructions.
- Python for local file, image, PDF, Excel, and data-processing scripts.
- TypeScript for API clients, schema validation, structured tool interfaces, MCP/tooling layers, and web/HTML/PDF orchestration.
- PowerShell or Shell only as thin OS-specific wrappers.

Keep `SKILL.md` concise. Move long guidance to `references/` and deterministic work to `scripts/`.