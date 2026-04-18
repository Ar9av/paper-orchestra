# Handoff Schemas — Data Contracts Between Pipeline Steps

Each schema defines the contract between a producing step and its consumers.
Consumers MUST validate on receipt. Missing required fields produce a
`HANDOFF_INCOMPLETE` error that halts the pipeline at the consuming step.

---

## Schema 1 — Outline → Steps 2 and 3

**File:** `workspace/outline.json`
**Producer:** outline-agent (Step 1)
**Consumers:** plotting-agent (Step 2), literature-review-agent (Step 3),
              section-writing-agent (Step 4)

```yaml
outline.json:
  plotting_plan:                      # REQUIRED — array, min 1 item
    - figure_id: string               # unique identifier, e.g. "fig_main_result"
      figure_type: string             # "bar"|"line"|"scatter"|"heatmap"|"diagram"|"other"
      caption_hint: string            # what the figure should show
      data_source: string             # which section of experimental_log.md to use
      required_by_section: string     # which section references this figure

  intro_related_work_plan:            # REQUIRED
    keywords: [string]                # list of search terms for Semantic Scholar
    target_citations: integer         # minimum number of citations to gather (e.g. 20)
    temporal_cutoff: date             # ISO date string, e.g. "2024-01-01" — exclude papers before

  section_plan:                       # REQUIRED — array, min 1 item
    - title: string                   # section title matching template.tex
      subsections: [string]           # list of subsection titles (may be empty)
      content_hints: string           # what this section must cover
      figure_ids: [string]            # figure_ids from plotting_plan used in this section
```

**HANDOFF_INCOMPLETE triggers:**
- `plotting_plan` missing or empty array
- `intro_related_work_plan` missing any of: `keywords`, `target_citations`, `temporal_cutoff`
- `section_plan` missing or empty array
- Any `figure_id` in `section_plan[].figure_ids` not present in `plotting_plan`

---

## Schema 2 — Steps 2 and 3 → Step 4

**Files:** `workspace/figures/`, `workspace/refs.bib`,
           `workspace/citation_pool.json`, `workspace/drafts/intro_relwork.tex`
**Producers:** plotting-agent (Step 2), literature-review-agent (Step 3)
**Consumer:** section-writing-agent (Step 4)

```yaml
figures/:                             # REQUIRED directory
  <figure_id>.png:                    # REQUIRED — one file per figure_id in outline.plotting_plan
    format: PNG
    min_size_bytes: 1024              # non-empty file check

  captions.json:                      # REQUIRED
    <figure_id>: string               # caption text for each figure; every figure_id must have entry

refs.bib:                             # REQUIRED
  format: valid BibTeX
  min_entries: 1
  constraints:
    - every entry has: author, title, year
    - every key referenced in citation_pool.json exists here

citation_pool.json:                   # REQUIRED — array
  - bibtex_key: string                # matches a key in refs.bib
    semantic_scholar_id: string       # S2 paper ID (may be null if DOI present)
    doi: string                       # DOI (may be null if semantic_scholar_id present)
    title: string
    year: integer
    venue: string                     # conference or journal name
    abstract: string                  # abstract text for hallucination checking (Schema 5 / failure mode 2)

drafts/intro_relwork.tex:             # REQUIRED
  format: valid LaTeX fragment
  must_contain: "\\section"           # at least one section command
  must_not_contain: "PLACEHOLDER"     # no unfilled placeholders
```

**HANDOFF_INCOMPLETE triggers:**
- Any `figure_id` from `outline.plotting_plan` missing its `.png` file
- `captions.json` missing or missing an entry for any `figure_id`
- `refs.bib` missing or empty
- `citation_pool.json` missing or empty array
- `drafts/intro_relwork.tex` missing
- A `bibtex_key` in `citation_pool.json` not present in `refs.bib`

---

## Schema 3 — Step 4 → Step 5

**File:** `workspace/drafts/paper.tex`
**Producer:** section-writing-agent (Step 4)
**Consumer:** content-refinement-agent (Step 5)

```yaml
drafts/paper.tex:                     # REQUIRED
  format: complete LaTeX document
  must_contain:
    - "\\begin{document}"
    - "\\end{document}"
    - "\\begin{abstract}"
    - "\\section"                     # at least one section

  citation_integrity:
    - every \\cite{KEY} must have KEY present in refs.bib
    - orphaned \\cite{}: HANDOFF_INCOMPLETE

  reference_integrity:
    - every \\ref{LABEL} must have a corresponding \\label{LABEL} in the document
    - orphaned \\ref{}: HANDOFF_INCOMPLETE

  table_formatting:
    - all tables containing numeric results must use booktabs package commands:
        \\toprule, \\midrule, \\bottomrule
    - standard \\hline-only tables for result tables: HANDOFF_INCOMPLETE

  no_placeholders:
    - document must not contain: "TODO", "FIXME", "PLACEHOLDER", "XX", "???"
```

**HANDOFF_INCOMPLETE triggers:**
- Missing `\begin{document}` or `\end{document}`
- Any `\cite{KEY}` where KEY is absent from `refs.bib`
- Any `\ref{LABEL}` where LABEL has no matching `\label{LABEL}`
- Result tables using `\hline` instead of booktabs commands

---

## Schema 4 — Step 5 → final/

**Files:** `workspace/final/paper.tex`, `workspace/final/paper.pdf`,
           `workspace/refinement/worklog.json`
**Producer:** content-refinement-agent (Step 5)
**Consumer:** paper-orchestra orchestrator (final report)

```yaml
final/paper.tex:                      # REQUIRED
  same constraints as Schema 3        # all Schema 3 checks apply to final output

final/paper.pdf:                      # REQUIRED
  format: valid PDF
  min_size_bytes: 10240               # non-trivial compiled document

refinement/worklog.json:              # REQUIRED
  format: JSON array
  min_entries: 1
  entry_schema:
    - iteration: integer              # 0-based; 0 = initial snapshot pre-refinement
      scores_before:                  # score.json of iter<N-1>
        scientific_depth: integer     # 0–100
        technical_execution: integer
        logical_flow: integer
        writing_clarity: integer
        evidence_presentation: integer
        academic_style: integer
      scores_after:                   # score.json of iter<N>
        scientific_depth: integer
        technical_execution: integer
        logical_flow: integer
        writing_clarity: integer
        evidence_presentation: integer
        academic_style: integer
      changes_summary: string         # human-readable description of what changed
      decision: "accept"|"revert"|"halt"
      da_critical: boolean            # optional — true if DA reviewer issued a CRITICAL finding
      failure_mode: integer           # optional — failure mode number if decision is "halt"
```

**HANDOFF_INCOMPLETE triggers:**
- `final/paper.tex` or `final/paper.pdf` missing
- `worklog.json` missing or empty array
- Any worklog entry missing `iteration`, `decision`, or `changes_summary`

---

## Schema 5 — Input Validation (workspace/inputs/)

**Files:** `workspace/inputs/` directory
**Validated by:** `scripts/validate_inputs.py` and `scripts/check_idea_density.py`
**Consumed by:** all pipeline steps

```yaml
inputs/idea.md:                       # REQUIRED
  min_words: 50
  must_contain_one_of:
    - "hypothesis"
    - "propose"
    - "method"
    - "approach"
    - "contribution"

inputs/experimental_log.md:           # REQUIRED
  min_markdown_tables: 1              # at least one table with |---| separator
  min_numeric_values: 5               # at least 5 numbers in the document
  not_duplicate_of_idea_md:           # Jaccard similarity on tokens < 0.5
    threshold: 0.5

inputs/template.tex:                  # REQUIRED
  format: valid LaTeX preamble
  must_contain:
    - "\\documentclass"
    - "\\begin{document}"

inputs/conference_guidelines.md:      # REQUIRED
  must_contain_one_of:
    - "page limit"
    - "pages"
    - "page count"
    - "maximum"

inputs/style_profile.md:             # OPTIONAL — author voice calibration
  purpose: >
    Describes the target author's writing preferences, preferred citation style,
    section structure preferences, and any venue-specific idioms.
    If absent, the pipeline uses default academic writing conventions.
```

**HANDOFF_INCOMPLETE triggers:**
- Any REQUIRED file missing from `inputs/`
- `idea.md` word count < 50
- `idea.md` contains none of the required hypothesis signals
- `experimental_log.md` contains no markdown tables
- `template.tex` missing `\documentclass`
- `conference_guidelines.md` contains no reference to page limits
