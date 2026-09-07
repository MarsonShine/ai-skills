---
name: write-natural-prose
description: "Draft or rewrite articles, documentation, explanations, and code comments in a natural contextual voice. Not for translation or contract audits; combine with specialist artifacts only for an explicit voice adjustment."
---

# Write Natural Prose

Write prose that follows a concrete train of thought instead of sounding assembled from a generic template. Preserve the user's meaning, facts, and constraints.

## Choose the Language

Use the strongest available evidence, in this order:

1. The language explicitly requested by the user.
2. The language of the target file or source text being edited.
3. The predominant language of nearby documents, the same module, or comparable files.
4. Repository conventions in README, contribution guidance, or other project instructions.
5. Chinese when the available context is still insufficient.

The language used to ask the question is not decisive by itself. In a mixed-language project, follow the target file and its nearest relevant peers; do not translate unrelated content merely to make the repository uniform.

## Writing Principles

Treat the examples as illustrations, not phrases to repeat.

1. **Begin with a concrete problem or trigger.** Skip generic scene-setting that does not help the reader understand what follows.  
   Example: “缓存命中了，接口却没有变快。问题不在查找，而在命中后仍要反序列化。”
2. **Move along time or causality.** Let one fact create the need for the next instead of forcing the material into symmetrical sections.  
   Example: “Requests are merged first and split only after a failure. One failed batch can therefore affect dozens of jobs.”
3. **Make examples advance the argument.** Use them to expose a tradeoff, consequence, or counterexample rather than decorate an abstract claim.  
   Example: “100 个请求合成一批，确实少了 99 次握手；但一个参数非法，整批回滚的代价也会一起放大。”
4. **State premises, scope, and strength of evidence.** Distinguish what the evidence shows from what remains unproven.  
   Example: “This proves only that the sample contains no collisions; it does not establish concurrency safety.”
5. **Use the target language's own natural syntax.** Prefer direct verbs and idiomatic rhythm over nominalized, translation-shaped sentences.  
   Chinese: change “对缓存策略的调整进行了实施” to “我们调整了缓存策略”. English: change “An adjustment of the cache policy was performed” to “We adjusted the cache policy.”

## Adapt to the Artifact

- For personal or opinion writing, use only experiences the user supplied. First person, contrast, and light self-deprecation are optional tools, not a house style; never invent personal details.
- For technical articles and documentation, normally progress from the problem through a constraint or distinction, reasoning, an example, and the boundary of the conclusion. This is a thought sequence, not a required set of headings.
- For code comments, match the current file's language and comment style. Explain only non-obvious reasons, preconditions, or consequences; do not narrate what the code already says.

## Boundaries

- Accuracy outranks fluency. Do not weaken or omit API contracts, security conditions, error behavior, compliance language, or other load-bearing details to make prose sound casual.
- Do not force rhetorical questions, jokes, reader address, personal anecdotes, or template conclusions. Do not fabricate facts, evidence, experiences, or certainty.
- Route ordinary English-to-Chinese translation to `translate-tech-en-zh`, contract-preserving technical prose review to `review-technical-prose`, and maintenance of an existing bilingual document pair to `sync-bilingual-docs`.
- Let specialist skills own the structure and requirements of resumes, business solutions, and other specialized artifacts. Apply this skill alongside them only when the user explicitly requests a natural-voice adjustment, and never override their factual or contractual constraints.
- The supplied examples establish Chinese expression preferences and general reasoning habits. For English, follow idiomatic English and project precedent; do not claim to reproduce an unobserved personal English style.
