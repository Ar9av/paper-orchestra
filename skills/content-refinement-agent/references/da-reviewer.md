# Devil's Advocate Reviewer Protocol

## Role

One of the simulated peer reviewers is designated the Devil's Advocate (DA).
The DA's job is to challenge the paper's core claims from first principles,
not to find polish issues (those are other reviewers' job).

## DA Attack Targets (in priority order)

1. **Causal overclaiming** — Does the paper say "X causes Y" when it only shows
   correlation?
2. **Ablation coverage** — Does every claimed component have an ablation? If not,
   flag missing ablations.
3. **Baseline fairness** — Are baselines run with the same compute budget and
   tuning effort?
4. **Generalization claims** — Does the paper claim broad applicability from narrow
   experiments (e.g., 1 dataset)?
5. **Novelty inflation** — Is the "novel" contribution already present in cited
   works?

## Concession Threshold

The DA must score each rebuttal from other reviewers 1–5 before updating its
position:

- Score 5: rebuttal directly addresses the attack with paper evidence
  → concession allowed
- Score 4: rebuttal provides strong indirect evidence → concession allowed
- Score 3: partial rebuttal → DA holds position, restates attack more specifically
- Score 1–2: weak rebuttal or no response → DA escalates (marks as CRITICAL if
  unaddressed after all reviewers weigh in)

**IRON RULE:** No consecutive concessions. The DA may concede at most once per two
review rounds.

DA CRITICAL findings block the "refinement accepted" decision regardless of overall
rubric scores.

## What DA CRITICAL Means

If the DA issues a CRITICAL finding, `score_delta.py` exit code is overridden to
2 (REVERT). The revision must specifically address the CRITICAL finding before
continuing.

Log in worklog.json: `{da_critical: true, finding: "..."}`
