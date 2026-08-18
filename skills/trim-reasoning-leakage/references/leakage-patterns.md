# Reasoning Leakage Patterns

Every search hit needs semantic judgment.

## Taxonomy

1. **Dead private references:** “decision 7,” “audit C2,” “plan section 4,” draft phase labels, or unnamed design ledgers that do not resolve in the repository.
2. **PR and stack vantage:** “this PR adds,” “a later PR,” “the previous commit,” or other positions that durable docs cannot see.
3. **Change narration:** “used to,” “no longer,” “the old implementation,” “now,” or indexical version stamps when current behavior can be stated directly.
4. **Review choreography:** reviewer verdicts, review rounds, draft ordinals, and appeals to reviewer authority.
5. **Reviewer-directed defense:** “this is safe because” when the maintainable fact is an invariant or the code already proves it.
6. **Derivation transcript:** line-by-line control-flow narration, obvious proofs, and test walkthroughs.
7. **Planning residue:** “probably,” “for now,” “should be enough,” and unowned future work.
8. **Working-language residue:** private separators, mixed-language drafting fragments, and references to uncommitted mockups.

## Recall Searches

Adapt terms and exclusions to the repository. Search hidden instruction or decision directories when they are in scope, while excluding vendor trees, frozen archives, snapshots, fixtures, and this skill's example files.

Useful English probes include `this PR`, `later PR`, `previous commit`, `used to`, `no longer`, `for now`, `reviewer`, `review round`, `decision [0-9]`, `audit [A-Z][0-9]`, and internal section ordinals. Useful Chinese probes include `设计稿`, `评审`, `上一轮`, `旧版`, `不再`, `本版`, `遗留`, and private separators.

Confirm each pattern against a known positive before trusting a zero-result search.

## Common False Positives

- “the key used to sign” is instrumental, not historical.
- “the old connection drains before the new one accepts” describes concurrent runtime objects.
- `v1` may be a protocol or URL identifier.
- RFC sections, issue numbers, committed decision links, and named external design frames can be intentional resolvable evidence.
- Recorded output preserves the voice of the recording.
