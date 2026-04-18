# AI Research Failure Modes Gate

Full checklist: `skills/shared/ai_failure_modes.md`

## When to Run

Run this gate ONCE at the start of the FIRST refinement iteration only.
It is a pre-refinement integrity check, not a per-iteration check.

## Decision Protocol

- **CONFIRMED failure (any mode 1–7):** HALT. Do not proceed to refinement.
  Report: which failure mode, what evidence, what the user must fix in the inputs.
  Write a HALT entry to worklog.json:
  `{iteration: 0, decision: "halt", reason: "...", failure_mode: N}`

- **SUSPECTED failure:** Add a WARNING comment at the top of paper.tex:
  `% WARNING: Potential failure mode N detected: [description]. Verify before submission.`
  Continue refinement but log the suspicion in worklog.json.

- **No failures:** Proceed to refinement iteration 1.
