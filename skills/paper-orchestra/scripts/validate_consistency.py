#!/usr/bin/env python3
"""
validate_consistency.py — Cross-validate idea.md vs experimental_log.md.

Checks for semantic consistency between the stated research idea and the
experimental results. Exits with code 1 (WARN) if issues are found, 0 (PASS)
otherwise.

Note: file-not-found errors should be caught upstream by check_idea_density.py.
This script assumes files exist.

Exit codes:
  0 — PASS: all checks passed (warnings may still be printed at PASS level)
  1 — WARN: one or more consistency issues found (non-blocking)
"""

import argparse
import re
import sys


def extract_metric_names(log_text: str) -> list:
    """
    Extract metric names from markdown table headers in experimental_log.md.
    Heuristic: words appearing before ':' or '|' in table header rows,
    that look like metric names (capitalized or standard ML metric patterns).
    Also extracts column headers from markdown tables.
    """
    metrics = set()

    # Extract table header rows (rows before |---|)
    # A table header is a row of |...|...|..| followed by a separator row
    table_header_pattern = re.compile(
        r"^\|(.+)\|\s*$\n\|[-| :]+\|", re.MULTILINE
    )
    for match in table_header_pattern.finditer(log_text):
        header_row = match.group(1)
        # Split by | and clean each cell
        cells = [c.strip() for c in header_row.split("|") if c.strip()]
        for cell in cells:
            # Keep cells that look like metric names:
            # - Contains letters
            # - Reasonable length (2-30 chars)
            # - Not purely numeric
            if re.match(r"^[A-Za-z][\w\s\-@%]*$", cell) and 2 <= len(cell) <= 30:
                metrics.add(cell.strip())

    # Also extract words before ':' that appear in context suggesting metrics
    metric_colon_pattern = re.compile(
        r"\b([A-Z][a-zA-Z0-9\-@%]{1,20})\s*:", re.MULTILINE
    )
    for match in metric_colon_pattern.finditer(log_text):
        candidate = match.group(1)
        # Filter to likely metric names (avoid common non-metric words)
        non_metrics = {
            "Note", "Warning", "Error", "Table", "Figure", "Section",
            "Results", "Setup", "Config", "Method", "Model", "Dataset",
            "Baseline", "Experiment", "Run", "Step", "Epoch", "Loss",
        }
        if candidate not in non_metrics:
            metrics.add(candidate)

    return list(metrics)


def extract_dataset_names(log_text: str) -> list:
    """
    Extract dataset/benchmark names from experimental_log.md.
    Heuristic: capitalized words (3+ chars, title-case or all-caps) appearing
    near keywords: dataset, on, benchmark, evaluated, trained on, tested on.
    """
    datasets = set()

    # Look for patterns like "on CIFAR-10", "evaluated on ImageNet", etc.
    dataset_context_pattern = re.compile(
        r"(?:dataset|benchmark|evaluated\s+on|trained\s+on|tested\s+on|on\s+the)\s+"
        r"([A-Z][A-Za-z0-9\-_]{2,30}(?:\s*[-/]\s*[A-Za-z0-9]+)?)",
        re.IGNORECASE,
    )
    for match in dataset_context_pattern.finditer(log_text):
        candidate = match.group(1).strip()
        # Must start with capital letter and be title-case or contain digits
        if re.match(r"^[A-Z]", candidate) and len(candidate) >= 3:
            datasets.add(candidate)

    # Also look for all-caps acronyms that are likely dataset names (3-10 chars)
    allcaps_pattern = re.compile(r"\b([A-Z]{3,10}(?:-[A-Z0-9]+)?)\b")
    # Only in table contexts
    table_lines = [
        line for line in log_text.split("\n") if "|" in line and "---" not in line
    ]
    for line in table_lines:
        for match in allcaps_pattern.finditer(line):
            candidate = match.group(1)
            # Filter out common non-dataset all-caps words
            exclude = {
                "GPU", "CPU", "RAM", "SSD", "API", "LLM", "NLP", "CV", "ML",
                "DL", "AI", "SGD", "RNN", "CNN", "GAN", "VAE", "BERT",
                "TODO", "FIXME", "NOTE", "MAX", "MIN", "AVG", "STD",
            }
            if candidate not in exclude:
                datasets.add(candidate)

    return list(datasets)


def count_nonzero_numerics_per_table(log_text: str) -> dict:
    """
    For each markdown table, count how many non-zero numeric values appear.
    Returns dict mapping table_index (1-based) to count of non-zero values.
    """
    results = {}
    # Split into table blocks
    table_pattern = re.compile(
        r"((?:^\|.+\|\s*$\n)+)", re.MULTILINE
    )
    for i, match in enumerate(table_pattern.finditer(log_text), start=1):
        table_text = match.group(1)
        numerics = re.findall(r"-?\d+\.?\d*", table_text)
        nonzero = [n for n in numerics if float(n) != 0.0]
        results[i] = len(nonzero)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Cross-validate idea.md vs experimental_log.md for consistency"
    )
    parser.add_argument("--idea", required=True, help="Path to idea.md")
    parser.add_argument("--log", required=True, help="Path to experimental_log.md")
    args = parser.parse_args()

    # Load files (file-not-found handled by check_idea_density.py upstream)
    try:
        with open(args.idea, "r", encoding="utf-8") as f:
            idea_text = f.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {args.idea}", file=sys.stderr)
        print("Run check_idea_density.py first to validate file existence.")
        sys.exit(1)

    try:
        with open(args.log, "r", encoding="utf-8") as f:
            log_text = f.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {args.log}", file=sys.stderr)
        print("Run check_idea_density.py first to validate file existence.")
        sys.exit(1)

    warnings = []
    idea_lower = idea_text.lower()

    # Check 1: metric names from log appear in idea
    metrics = extract_metric_names(log_text)
    if metrics:
        matched_metrics = [m for m in metrics if m.lower() in idea_lower]
        if matched_metrics:
            print(
                f"[PASS] Metric alignment: {len(matched_metrics)}/{len(metrics)} "
                f"metrics from log found in idea.md "
                f"(e.g., {matched_metrics[:3]})"
            )
        else:
            print(
                f"[WARN] Metric alignment: 0/{len(metrics)} metrics from "
                f"experimental_log.md appear in idea.md"
            )
            print(f"       Metrics detected in log: {metrics[:10]}")
            print(
                "       The idea should mention what it's measuring. "
                "Verify the idea describes the same evaluation as the experiments."
            )
            warnings.append("No metrics from experimental_log.md found in idea.md")
    else:
        print(
            "[WARN] Metric extraction: no metric names detected in "
            "experimental_log.md tables — check table formatting"
        )
        warnings.append("Could not extract metric names from experimental_log.md")

    # Check 2: dataset names from log appear in idea (>=50%)
    datasets = extract_dataset_names(log_text)
    if datasets:
        matched_datasets = [d for d in datasets if d.lower() in idea_lower]
        coverage = len(matched_datasets) / len(datasets)
        if coverage >= 0.5:
            print(
                f"[PASS] Dataset alignment: {len(matched_datasets)}/{len(datasets)} "
                f"datasets from log found in idea.md ({coverage:.0%} coverage)"
            )
        else:
            print(
                f"[WARN] Dataset alignment: {len(matched_datasets)}/{len(datasets)} "
                f"datasets from log found in idea.md ({coverage:.0%} coverage, need >=50%)"
            )
            missing = [d for d in datasets if d.lower() not in idea_lower]
            print(f"       Datasets in log not mentioned in idea: {missing[:5]}")
            warnings.append(
                f"Only {coverage:.0%} of datasets from log mentioned in idea.md"
            )
    else:
        print(
            "[WARN] Dataset extraction: no dataset names detected in "
            "experimental_log.md — check that dataset names appear in table context"
        )
        warnings.append("Could not extract dataset names from experimental_log.md")

    # Check 3: no table has all-zero results
    table_nonzero = count_nonzero_numerics_per_table(log_text)
    if table_nonzero:
        all_zero_tables = [
            idx for idx, count in table_nonzero.items() if count == 0
        ]
        if all_zero_tables:
            print(
                f"[WARN] Zero-result tables: table(s) {all_zero_tables} contain "
                f"only zero or no numeric values — verify results are present"
            )
            warnings.append(
                f"Tables {all_zero_tables} have no non-zero numeric results"
            )
        else:
            total_tables = len(table_nonzero)
            print(
                f"[PASS] Result coverage: all {total_tables} table(s) contain "
                f"at least one non-zero numeric value"
            )
    else:
        # No tables found — this should be caught by check_idea_density.py
        print(
            "[WARN] No tables found in experimental_log.md — "
            "run check_idea_density.py to verify table count"
        )
        warnings.append("No tables found in experimental_log.md")

    # Summary
    print()
    if not warnings:
        print("Consistency check: PASS")
        sys.exit(0)
    else:
        print(f"Consistency check: WARN ({len(warnings)} issue(s) found — non-blocking)")
        for w in warnings:
            print(f"  - {w}")
        print(
            "\nThese are warnings, not errors. The pipeline will continue. "
            "Address warnings before submission."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
