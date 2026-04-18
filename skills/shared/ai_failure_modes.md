# AI Research Failure Modes Gate

This is a **BLOCKING gate**. Any CONFIRMED failure halts paper production.

Run this gate ONCE at the start of the FIRST refinement iteration. It is a
pre-refinement integrity check, not a per-iteration check.

---

## Decision Protocol

- **CONFIRMED failure (any mode 1–7):** HALT. Do not proceed to refinement.
  Report: which failure mode, what evidence, what the user must fix in the inputs.
  Write a HALT entry to worklog.json:
  `{iteration: 0, decision: "halt", reason: "...", failure_mode: N}`

- **SUSPECTED failure:** Add a WARNING comment at the top of paper.tex:
  `% WARNING: Potential failure mode N detected: [description]. Verify before submission.`
  Continue refinement but log the suspicion in worklog.json.

- **No failures:** Proceed to refinement iteration 1.

---

## Failure Mode 1 — Implementation Bug Passing Self-Review

**Check:** Does the method description in the paper match the experimental_log.md
code snippets exactly?

- Every claimed hyperparameter (learning rate, batch size, hidden dimensions,
  optimizer, number of layers, etc.) must appear verbatim or with numeric
  equivalence in experimental_log.md.
- If the paper describes "a two-layer transformer with 512 hidden units" but
  experimental_log.md shows `hidden_dim=256`, this is CONFIRMED.
- If experimental_log.md contains no code snippets at all, flag as SUSPECTED.

**Why it matters:** Self-review by the generating model does not catch
implementation-description mismatches because the model defaults to reproducing
the description it just wrote rather than grounding it in the log.

---

## Failure Mode 2 — Hallucinated Citation

**Check:** Every `\cite{KEY}` in the paper must have a corresponding entry in
refs.bib. Every entry in refs.bib must have either a `semantic_scholar_id` field
or a verified DOI.

Additionally: every factual claim attributed to a citation (e.g., "Smith et al.
[3] showed that X achieves 92% accuracy on Y") must be traceable to the cited
paper's abstract or body as present in citation_pool.json.

- CONFIRMED: a `\cite{KEY}` key that does not exist in refs.bib.
- CONFIRMED: a specific numeric claim attributed to a citation that contradicts or
  does not appear in that citation's abstract in citation_pool.json.
- SUSPECTED: a citation entry in refs.bib with neither semantic_scholar_id nor DOI.

**Why it matters:** LLMs generate plausible-sounding citations and attribute
claims to them without verifying the actual content of the cited work.

---

## Failure Mode 3 — Hallucinated Experimental Result

**Check:** Every numeric result in the paper body (tables, figures, and inline
claims) must appear verbatim in experimental_log.md.

- Rounding is permitted only up to 2 significant figures. Any rounding beyond this
  must be explicitly disclosed ("reported to 2 s.f.").
- CONFIRMED: a number in the paper that does not appear in experimental_log.md and
  cannot be derived from any number in experimental_log.md by standard rounding.
- SUSPECTED: a number that can be derived by non-standard rounding (e.g., 0.7321
  reported as 0.74 without disclosure).

**Why it matters:** Models interpolate or fabricate numeric results when the actual
results are not salient in the input context, particularly in long papers where
the experimental log is referenced early but not kept in the near context window.

---

## Failure Mode 4 — Shortcut Reliance

**Check:** If the paper claims "our method outperforms baseline X" or "removing
component Y hurts performance," an ablation experiment removing that component must
be present in experimental_log.md.

- CONFIRMED: a claim of the form "X is essential / critical / key to performance"
  with no corresponding ablation row in experimental_log.md.
- SUSPECTED: a claim "X improves performance" where no comparison to a variant
  without X is present.

**Why it matters:** Models learn to generate ablation claims as a stylistic
convention of ML papers without requiring the actual ablation to exist in the
inputs.

---

## Failure Mode 5 — Bug Reframed as Novel Insight

**Check:** Flag any sentence containing "surprisingly" or "unexpectedly" (case-
insensitive) that is not accompanied by a citation supporting that the finding is
indeed surprising or unexpected relative to prior work.

- CONFIRMED: "Surprisingly, our model achieves better results with less data" with
  no citation to prior work establishing the expected relationship.
- SUSPECTED: use of "surprisingly" / "unexpectedly" with a citation that does not
  actually establish a contrary expectation.

**Why it matters:** When a model's experimental results contain anomalies (often
from bugs), the generating LLM reframes them as novel discoveries rather than
flagging them as potential errors. "Surprising" results should be treated as
signals to double-check the experimental log, not marketing language.

---

## Failure Mode 6 — Methodology Fabrication

**Check:** Every numerical parameter stated in the Methodology section of the paper
must match actual run configurations in experimental_log.md.

Parameters to check specifically:
- Learning rate
- Batch size
- Number of epochs / training steps
- Architecture dimensions (layers, hidden size, heads, etc.)
- Optimizer name and any stated hyperparameters (momentum, weight decay, etc.)
- Dataset split sizes (train/val/test counts or percentages)

- CONFIRMED: any stated parameter that contradicts the corresponding value in
  experimental_log.md.
- CONFIRMED: any parameter stated in Methodology that is entirely absent from
  experimental_log.md (no matching field anywhere).

**Why it matters:** The Methodology section is generated from the model's prior
over what reasonable hyperparameters look like, not from the actual experimental
configuration, unless the generating prompt explicitly enforces cross-referencing.

---

## Failure Mode 7 — Frame-Lock at Early Stage

**Check:** Compare the core framing of the paper (thesis sentence, abstract,
introduction's contribution list) to:
1. The framing in idea.md
2. The current experimental_log.md

- CONFIRMED: the paper's abstract or introduction is a near-verbatim restatement
  of idea.md's hypothesis, and experimental_log.md contains results that
  contradict, qualify, or supersede that hypothesis without those updates being
  reflected in the paper.
- SUSPECTED: the paper's framing matches idea.md but experimental_log.md contains
  substantial findings not referenced anywhere in the introduction or abstract.

**Concrete checks:**
- Does the abstract mention the main metric reported in experimental_log.md?
- Does the contribution list in the introduction match what was actually built,
  as evidenced by experimental_log.md?
- If experimental_log.md contains a section describing a changed approach (e.g.,
  "we abandoned method A in favor of method B"), does the paper still describe
  method A as the primary approach?

**Why it matters:** Models anchor on the first framing they see (idea.md) and do
not spontaneously update the narrative when experimental evidence diverges from the
original hypothesis. The result is a paper whose framing misrepresents the actual
work.
