# Decision Record Lifecycle Guidance

Use repository-specific terminology in the final work. The categories below are analytical aids, not a replacement lifecycle.

## Classification

- **Active:** still owns a current mechanism, constraint, compatibility promise, security rule, rejected alternative, or future decision.
- **Partially superseded:** a newer owner replaces part of the decision, while some rationale or supported behavior remains current. Keep and cross-link it unless local rules provide a formal split.
- **Fully superseded:** no production behavior, format, migration, compatibility path, or independently useful rationale remains unique to the older record.
- **Implemented with future value:** implementation is complete, but the alternatives, negative guarantees, ownership rules, or reintroduction conditions may guide later changes.
- **Archival candidate:** implementation is complete, current behavior is authoritative elsewhere, and the record's remaining detail is mainly closed implementation history.
- **Removable rejection:** the rejected idea is obsolete, no longer plausible, or fully answered by a newer decision.

## Supersession Test

Before declaring full supersession, search for:

- the record filename and title;
- named APIs, config keys, events, wire fields, and storage formats;
- tests that enforce supported or intentionally absent behavior;
- inbound links from active docs and code comments;
- newer records that claim ownership of the same decision.

Full supersession requires a current owner for every unique rationale, alternative, consequence, and compatibility obligation worth preserving. A newer date or similar title is not enough.

## Archive and Removal

Follow the local mechanics exactly: required status changes, dates, directory moves, companion files, hashes, manifests, and append-only seals. If the repository has no mechanics, do not create an archive convention during an ordinary audit.

For removal, update or remove inbound links in the same change. Do not follow a link-cleanup pass into frozen archived content unless the archive policy explicitly permits edits.

## Borderline Cases

Defer when two records could reasonably become the owner, when archival changes review or compliance history, or when a supposedly obsolete format may still exist in durable data. Present the alternatives and the evidence that would resolve the choice.
