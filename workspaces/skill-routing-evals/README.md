# Skill Routing Evaluations

These cases test first-layer skill discovery. They evaluate the complete catalog of skill `name` and `description` values without preloading any `SKILL.md` body.

## Case Contract

Each case contains:

- `id`: stable case identifier;
- `prompt`: the only user request presented to the routing pass;
- `expected_skills`: the exact repository skills that should be selected;
- `forbidden_skills`: skills whose selection is a routing failure; and
- `reason`: the intent boundary the case protects.

An empty `expected_skills` array means the repository plugin should not claim the request. The runtime may still use a built-in skill or ordinary model behavior.

## Evaluation Procedure

1. Build the catalog from every direct `skills/*/SKILL.md` frontmatter entry.
2. Start a fresh routing context containing only that catalog and one case prompt.
3. Record selected repository skills before loading any skill body.
4. Pass when the selected repository skills exactly match `expected_skills` and none appear in `forbidden_skills`.
5. Record the runtime, model, date, and unexpected selection for any failure.

Run the full corpus after metadata changes and again from a new Codex task after plugin reinstall. Do not weaken a near-miss case merely to increase aggregate recall; adjust the conflicting descriptions and rerun the complete catalog.
