# Writing Quality Check — Anti-AI-Prose Checklist

Apply this checklist at the start of each refinement iteration BEFORE generating
revision suggestions. Score the draft across all five categories, note violations,
and add them to the revision agenda. After applying revisions, re-check Categories
A and C (fastest) to confirm fixes landed.

**Never count "removed AI buzzwords" as a rubric scoring dimension.** It does not
raise rubric scores. Its purpose is to prevent polish masking weak content.

---

## Category A — High-Frequency AI Vocabulary

### What to detect

Flag any appearance of these 25 terms. Each use is a candidate for replacement or
removal — not an automatic deletion:

1. delve
2. tapestry
3. leverage (verb, non-technical)
4. nuanced
5. multifaceted
6. groundbreaking
7. transformative
8. embark
9. realm
10. foster
11. underscore (verb: "underscores the importance of")
12. synergy
13. holistic
14. robust (used as empty praise rather than statistical sense)
15. pivotal
16. seamlessly
17. streamline
18. cutting-edge
19. state-of-the-art (as filler without citation — "our state-of-the-art method")
20. notable
21. commendable
22. intricately
23. paramount
24. curated
25. elevate (verb: "elevates the contribution")

### Why it matters

These terms cluster in LLM-generated text because they are statistically
over-represented in web-scraped training corpora that praise products and
achievements. Peer reviewers pattern-match them as signals of thin content.

### What to do when flagged

**Rewrite, do not just remove.** Ask: what specific claim does this word obscure?
Replace with the specific claim.

- "Our method seamlessly integrates X and Y" → "Our method combines X and Y without
  an additional alignment step (see Section 3.2)."
- "This is a groundbreaking result" → state the numeric improvement and why it
  matters for the field.
- "We delve into the details" → delete the throat-clearing; start the detail.

---

## Category B — Punctuation Patterns

### What to detect

- **Em dashes (—):** count total in the paper. Flag if > 3.
- **Semicolons:** count per 1,000 words. Flag if > 2 per 1,000 words.

### Why it matters

Em dashes in AI prose typically signal inserted parenthetical asides that fragment
argument flow. Semicolons, when overused, indicate lists masquerading as prose.
Real academic writing uses these punctuation marks sparingly and purposefully.

### What to do when flagged

- Em dash excess: convert parenthetical asides into separate sentences or remove
  them if they restate what was just said.
- Semicolon excess: split the sentence or restructure as a numbered list if the
  content warrants enumeration.

---

## Category C — Throat-Clearing Openers

### What to detect

Flag any sentence that opens with (case-insensitive):

1. "It is worth noting that"
2. "It is important to note that"
3. "In the realm of"
4. "In the context of"
5. "It goes without saying"
6. "Needless to say"
7. "At the end of the day"
8. "In today's world"

### Why it matters

These openers defer meaning. They signal to reviewers that the following sentence
could not carry its own weight without a preamble. They are among the most
statistically diagnostic patterns in LLM-generated academic text.

### What to do when flagged

Delete the opener and start with the claim. Every flagged sentence can be rewritten
by starting at the word immediately after "that" or "of".

- "It is worth noting that our method converges faster" → "Our method converges
  faster..."
- "In the realm of computer vision, attention mechanisms have..." → "Attention
  mechanisms have..."

---

## Category D — Structural Patterns

### What to detect

Three structural patterns that signal templated generation:

1. **Forced Rule of Three:** every list in the paper has exactly 3 items. Flag if
   5 or more lists have exactly 3 items and no list has 2 or 4+ items.

2. **Uniform paragraph lengths:** compute word count of every paragraph. Flag if
   all paragraphs are within a 10-word band of each other (max - min < 10 words).

3. **Synonym cycling:** flag 3 or more paragraphs in close proximity (within 5
   paragraphs of each other) that use different words for the same concept to
   avoid apparent repetition — e.g., "precision", "accuracy", "exactness" in
   successive paragraphs when they refer to the same metric.

### Why it matters

Real academic writing reflects the irregular shape of ideas — some points require
2 items, some require 5. Uniform paragraph lengths indicate paragraph-by-paragraph
generation rather than argument-driven structure. Synonym cycling is a known
self-paraphrase artifact of autoregressive models.

### What to do when flagged

- Rule of Three: audit each list. Add or remove items based on what the content
  actually supports, not to achieve balance.
- Uniform paragraphs: identify which paragraphs are padded and trim them, or
  identify which are artificially short and expand the argument.
- Synonym cycling: pick one term per concept and use it consistently throughout the
  paper. Introduce synonyms only with an explicit definitional equivalence.

---

## Category E — Burstiness (Sentence-Length Variation)

### What to detect

Compute the word count of each sentence in the paper. Flag any run of 5 or more
consecutive sentences where every sentence falls within a 15-word band of the
others (max - min < 15 words across the run).

### Why it matters

Human academic prose exhibits high burstiness: a long complex sentence establishing
a claim is followed by a short sentence emphasizing the key implication, then
another longer sentence providing evidence. LLMs trained on diverse text produce
medium-length sentences consistently, resulting in low burstiness. Reviewers
describe this as prose that "reads like a machine."

### What to do when flagged

Identify the flagged run. Restructure to break the length band:

- Find the sentence carrying the most important claim in the run. Shorten it to
  a direct statement (5–12 words).
- Find the sentence with the most subordinate clauses. Split it.
- Alternatively, merge two adjacent sentences that each state a half-thought into
  one complex sentence.

The goal is not to introduce artificial length variation — it is to let the
importance of each claim determine its sentence weight.
