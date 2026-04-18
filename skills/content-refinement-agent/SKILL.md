---
name: content-refinement-agent
description: Step 5 of the PaperOrchestra pipeline (arXiv:2604.05018). Iteratively refine drafts/paper.tex by simulating peer review and applying targeted revisions, with strict accept/revert halt rules. Maintains a worklog and snapshots each iteration so revert is real, not symbolic. TRIGGER when the orchestrator delegates Step 5 or when the user asks to "refine the draft", "iterate on the paper", or "run peer review on this paper".
data_access_level: verified_only
---

# Content Refinement Agent (Step 5)

Faithful implementation of the Content Refinement Agent from PaperOrchestra
(Song et al., 2026, arXiv:2604.05018, §4 Step 5, App. F.1 pp. 49–51).

**Cost: ~5–7 LLM calls** (App. B), typically ~3 refinement iterations, each
consisting of one reviewer call and one revision call.

The paper highlights this step as one of the largest contributors to overall
quality: refinement alone accounts for +19% (CVPR) and +22% (ICLR) absolute
acceptance-rate improvement (Fig. 4). Get this step right.

## Inputs

- `workspace/drafts/paper.tex` — output of Step 4
- `workspace/inputs/conference_guidelines.md`
- `workspace/inputs/experimental_log.md` — used as ground truth for the
  hallucination check
- `workspace/citation_pool.json` / `workspace/refs.bib` — the allowed
  bibliography

## Outputs

- `workspace/refinement/iter1/`, `iter2/`, `iter3/` — per-iteration snapshots
  containing `paper.tex`, `paper.pdf`, `review.json`, `score.json`
- `workspace/refinement/worklog.json` — append-only history of decisions
- `workspace/final/paper.tex` and `workspace/final/paper.pdf` — copy of the
  best accepted snapshot

## The refinement loop

```
prev_score = score(paper.tex)                  # baseline from initial draft
snapshot iter0/

for iter in 1..ITER_CAP (default 3):
    1. simulate_review(paper.tex) → review.json
       (uses `references/reviewer-rubric.md` rubric)

    2. apply_revision(paper.tex, review.json) → new_paper.tex
       (uses verbatim Refinement Agent prompt at `references/prompt.md`)

    3. snapshot iter<N>/ with new_paper.tex, review.json
       latexmk -pdf new_paper.tex → iter<N>/paper.pdf

    4. score(new_paper.tex) → curr_score

    5. decide via score_delta.py:
       - if curr.overall > prev.overall:                       ACCEPT
       - elif curr.overall == prev.overall and net_subaxis ≥0: ACCEPT
       - else:                                                 REVERT

    6. apply_worklog.py to append the decision

    7. if REVERT or no actionable weaknesses or iter == ITER_CAP: HALT

    paper.tex ← new_paper.tex   (only on ACCEPT)
    prev_score ← curr_score

cp <best iter>/paper.tex → workspace/final/paper.tex
```

The "best" snapshot at HALT is the one with the highest accepted overall
score. On a REVERT halt, the best is the iteration immediately before the
revert.

## Step-by-step

### 0. Pre-refinement integrity gate

Before snapshotting or scoring the initial draft, run the AI failure modes gate:

Load `references/ai-failure-modes.md` (which points to `skills/shared/ai_failure_modes.md`).
Run all 7 checks against the draft and the inputs. This gate runs **once only**,
at the start of iteration 1.

- CONFIRMED failure → write HALT entry to worklog.json, report to user, stop.
- SUSPECTED failure → add WARNING comment to paper.tex, log in worklog.json, continue.
- No failures → proceed.

### 0b. Snapshot the initial draft

```bash
python skills/content-refinement-agent/scripts/snapshot.py \
    --src workspace/drafts/paper.tex \
    --dst workspace/refinement/iter0/
```

This creates `iter0/paper.tex`. Then compile to `iter0/paper.pdf`:


```bash
cd workspace/refinement/iter0/ && latexmk -pdf -interaction=nonstopmode paper.tex
```

Score it (see Step 1 below) → `iter0/score.json`.

### 1. Simulate peer review

For each iteration N starting from 1:

**Writing quality pre-check (start of every iteration):** Load
`references/writing-quality-check.md` and run the 5-category checklist
(Categories A–E) against the current draft. Note violations and add them to
the revision agenda.

Load `references/reviewer-rubric.md` as the system prompt for the simulated
reviewer call. The reviewer reads `iter<N-1>/paper.pdf` (or `paper.tex` if
your host LLM lacks PDF input) and produces a JSON of strengths,
weaknesses, questions, and per-axis scores.

The rubric is structured to mimic AgentReview (Jin et al., 2024) — the
paper's chosen evaluator. We ship a faithful rubric in the references
directory; the host agent's LLM does the actual reviewing.

**Devil's Advocate reviewer:** One simulated reviewer must be designated the DA
following `references/da-reviewer.md`. The DA challenges core claims from first
principles (causal overclaiming, ablation coverage, baseline fairness,
generalization claims, novelty inflation) rather than surface polish. If the DA
issues a CRITICAL finding that remains unaddressed after all reviewers weigh in,
that finding blocks the "refinement accepted" decision regardless of rubric scores.
Log DA CRITICAL findings in worklog.json: `{da_critical: true, finding: "..."}`.

Save to `workspace/refinement/iter<N>/review.json`.

### 2. Score the draft

The reviewer call produces both qualitative feedback and a per-axis score:

```json
{
  "axis_scores": {
    "scientific_depth":     {"score": 65, "justification": "..."},
    "technical_execution":  {"score": 70, "justification": "..."},
    "logical_flow":         {"score": 60, "justification": "..."},
    "writing_clarity":      {"score": 55, "justification": "..."},
    "evidence_presentation":{"score": 72, "justification": "..."},
    "academic_style":       {"score": 68, "justification": "..."}
  },
  "overall_score": 64.5,
  "strengths": [...],
  "weaknesses": [...],
  "questions": [...]
}
```

Save to `iter<N>/score.json`. (Combined with `review.json` if your host
emits one document; the schemas overlap.)

### 3. Apply revision

Load the **verbatim Content Refinement Agent prompt** at `references/prompt.md`.
Prepend the Anti-Leakage Prompt. Inputs:

- `paper.tex` — current draft
- `paper.pdf` — compiled PDF (multimodal context if available)
- `conference_guidelines.md`
- `experimental_log.md` — ground truth for numeric claims
- `worklog.json` — history of previous changes
- `citation_pool.json` — the allowed bibliography
- `reviewer_feedback` — the JSON from Step 1

The prompt instructs the model to address weaknesses, integrate question
answers, and emit two output blocks:

1. A worklog JSON `{addressed_weaknesses[], integrated_answers[], actions_taken[]}`
2. The full revised LaTeX code

Save the revised LaTeX as `iter<N>/paper.tex`. Append the worklog JSON to
`workspace/refinement/worklog.json` via `apply_worklog.py`.

### 4. Compile and re-score

```bash
cd workspace/refinement/iter<N>/ && latexmk -pdf -interaction=nonstopmode paper.tex
```

Then re-run the simulated review on the new draft → updated `score.json`
for the new iteration. (This is the "re-score after revision" call.)

### 5. Apply the accept/revert decision

The calling loop must track `CONSECUTIVE_SMALL` (starts at 0) and pass it
on each call so `score_delta.py` can detect the plateau:

```bash
python skills/content-refinement-agent/scripts/score_delta.py \
    --prev workspace/refinement/iter<N-1>/score.json \
    --curr workspace/refinement/iter<N>/score.json \
    --plateau-threshold 1.0 \
    --plateau-streak 3 \
    --consecutive-small $CONSECUTIVE_SMALL \
    > workspace/refinement/iter<N>/delta.json

EXIT=$?
# Update streak for next iteration:
CONSECUTIVE_SMALL=$(python3 -c "
import json
d = json.load(open('workspace/refinement/iter<N>/delta.json'))
print(d['consecutive_small'])
")
```

Exit codes:
- `0` — ACCEPT (overall improved or tied with non-negative net sub-axis, no plateau)
- `1` — REVERT (overall decreased)
- `2` — REVERT (tied overall, but net sub-axis change negative)
- `4` — HALT_PLATEAU (accepted but N consecutive iterations below threshold — stop early)

Behavior:

- **ACCEPT (exit 0)**: keep `iter<N>/paper.tex` as the new best. Continue to iter N+1.
- **REVERT (exit 1 or 2)**: copy `iter<N-1>/paper.tex` back as canonical, halt.
- **HALT_PLATEAU (exit 4)**: keep current (it was accepted), but stop — further
  iterations are unlikely to yield meaningful gains. In practice ~85% of
  refinement gain comes in iteration 1; the plateau fires when subsequent
  iterations improve by less than 1 point for 3 consecutive rounds.

Always log the decision via `apply_worklog.py --decision ...`.

### 6. Halt rules

Halt the loop when ANY of these is true:

1. Iteration count reaches `ITER_CAP` (default 3).
2. `score_delta.py` returned exit code 1 or 2 (REVERT).
3. The simulated reviewer's `weaknesses` list is empty (no actionable
   feedback to apply).
4. `score_delta.py` returned exit code 4 (HALT_PLATEAU — plateau early-stop).

### 7. Promote the best snapshot

Identify the iteration with the highest accepted `overall_score` (this may
be the latest accepted iteration, OR an earlier one if a later iteration
was reverted). Copy:

```bash
cp workspace/refinement/iter<best>/paper.tex workspace/final/paper.tex
cp workspace/refinement/iter<best>/paper.pdf workspace/final/paper.pdf
```

Then in the final report, tell the user:
- How many iterations were run
- The final overall score
- The score trajectory (e.g., "iter0 64.5 → iter1 67.3 (accept) → iter2 69.1 (accept) → iter3 68.9 (revert, halt)")
- Which iteration was promoted

## Critical safety constraints (App. F.1 page 50–51)

The paper explicitly notes that early versions of the Refinement Agent
"exploited the automated reviewer's scoring function by superficially
listing missing baselines as limitations to artificially inflate
acceptance scores." The verbatim prompt forbids this. **You must honor it:**

- **[IRON RULE] Halt on score regression.** If `score_delta.py` returns exit
  code 1 or 2 (REVERT), immediately revert to the previous snapshot and halt.
  No further revision attempts are permitted after a regression.
- **[IRON RULE] No new experiments in revision.** Ignore reviewer requests for
  new experiments, ablations, or baselines. The Refinement Agent's job is
  presentation, not new science. If the reviewer asks for missing data, simply
  skip those points — do NOT add fabricated experiments, do NOT add a "future
  work" item promising them.
- **[IRON RULE] All numeric claims must match experimental_log.md.** The agent
  cannot introduce new numbers, only re-present existing ones. Any number in
  the revised paper that does not appear in experimental_log.md is a
  hallucination.
- **Never explicitly state a limitation.** The phrase "we acknowledge as a
  limitation that..." is forbidden. The model can address weaknesses
  through clearer explanation, but must not game the evaluator by listing
  them defensively.

These rules prevent reward hacking and keep the refinement loop honest.

## Resources

- `references/prompt.md` — verbatim Content Refinement Agent prompt from App. F.1
- `references/reviewer-rubric.md` — AgentReview-style scoring rubric (6 axes)
- `references/halt-rules.md` — accept/revert/halt logic in formal pseudocode
- `references/safe-revision-rules.md` — anti-reward-hack constraints
- `references/writing-quality-check.md` — 5-category anti-AI-prose checklist (pointer to shared)
- `references/ai-failure-modes.md` — 7-mode integrity gate run before first iteration (pointer to shared)
- `references/da-reviewer.md` — Devil's Advocate reviewer protocol and concession rules
- `scripts/score_delta.py` — accept/revert decision from two score JSONs
- `scripts/score_trajectory.py` — per-dimension score history, regression and plateau detection
- `scripts/apply_worklog.py` — append iteration entries to worklog.json
- `scripts/snapshot.py` — copy paper.tex/paper.pdf into iter<N>/ for rollback
- `skills/shared/writing_quality_check.md` — full anti-AI-prose checklist (5 categories)
- `skills/shared/ai_failure_modes.md` — full AI research failure modes gate (7 modes)
- `skills/shared/handoff_schemas.md` — formal data contracts between all pipeline steps
