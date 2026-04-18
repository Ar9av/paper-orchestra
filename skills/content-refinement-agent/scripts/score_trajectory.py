#!/usr/bin/env python3
"""
score_trajectory.py — Track per-dimension score deltas across refinement iterations
and detect regression or plateau conditions.

Exit codes:
  0 — OK: no regression or plateau detected
  1 — REGRESSION or PLATEAU: issue detected (see output for details)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


DIMENSIONS = [
    "scientific_depth",
    "technical_execution",
    "logical_flow",
    "writing_clarity",
    "evidence_presentation",
    "academic_style",
]

COLUMN_WIDTH = 22


def load_scores(scores_dir: str) -> list:
    """
    Load all iterN/scores.json files from scores_dir in order.
    Returns list of (iter_number, scores_dict) sorted by iter_number.
    """
    scores_dir_path = Path(scores_dir)
    if not scores_dir_path.is_dir():
        print(f"[ERROR] scores-dir not found: {scores_dir}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for item in scores_dir_path.iterdir():
        match = re.match(r"^iter(\d+)$", item.name)
        if match and item.is_dir():
            scores_file = item / "scores.json"
            if scores_file.exists():
                try:
                    with open(scores_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    entries.append((int(match.group(1)), data))
                except (json.JSONDecodeError, IOError) as e:
                    print(
                        f"[WARN] Could not load {scores_file}: {e}",
                        file=sys.stderr,
                    )

    entries.sort(key=lambda x: x[0])
    return entries


def compute_overall(scores: dict) -> float:
    """Compute mean of all 6 dimensions."""
    values = [scores.get(d, 0) for d in DIMENSIONS]
    return sum(values) / len(values)


def compute_deltas(prev: dict, curr: dict) -> dict:
    """Compute per-dimension delta (curr - prev)."""
    return {d: curr.get(d, 0) - prev.get(d, 0) for d in DIMENSIONS}


def print_score_table(entries: list):
    """Print a formatted table of scores per dimension across iterations."""
    iter_labels = [f"iter{n}" for n, _ in entries]

    # Header
    header = f"{'Dimension':<{COLUMN_WIDTH}}" + "".join(
        f"{label:>10}" for label in iter_labels
    )
    print(header)
    print("-" * len(header))

    # Rows per dimension
    for dim in DIMENSIONS:
        row = f"{dim:<{COLUMN_WIDTH}}"
        for _, scores in entries:
            val = scores.get(dim, "N/A")
            if isinstance(val, (int, float)):
                row += f"{val:>10.1f}"
            else:
                row += f"{'N/A':>10}"
        print(row)

    # Overall row
    print("-" * len(header))
    overall_row = f"{'OVERALL':<{COLUMN_WIDTH}}"
    for _, scores in entries:
        overall = compute_overall(scores)
        overall_row += f"{overall:>10.1f}"
    print(overall_row)
    print()

    # Delta rows (if more than 1 iteration)
    if len(entries) > 1:
        print("Per-dimension deltas (current vs previous iteration):")
        delta_header = f"{'Dimension':<{COLUMN_WIDTH}}" + "".join(
            f"{f'Δ{iter_labels[i]}':>10}" for i in range(1, len(iter_labels))
        )
        print(delta_header)
        print("-" * len(delta_header))

        for dim in DIMENSIONS:
            row = f"{dim:<{COLUMN_WIDTH}}"
            for i in range(1, len(entries)):
                prev_scores = entries[i - 1][1]
                curr_scores = entries[i][1]
                delta = curr_scores.get(dim, 0) - prev_scores.get(dim, 0)
                sign = "+" if delta > 0 else ""
                row += f"{sign}{delta:>9.1f}"
            print(row)

        # Overall delta row
        overall_delta_row = f"{'OVERALL Δ':<{COLUMN_WIDTH}}"
        for i in range(1, len(entries)):
            prev_overall = compute_overall(entries[i - 1][1])
            curr_overall = compute_overall(entries[i][1])
            delta = curr_overall - prev_overall
            sign = "+" if delta > 0 else ""
            overall_delta_row += f"{sign}{delta:>9.1f}"
        print("-" * len(delta_header))
        print(overall_delta_row)
        print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Track score trajectory across refinement iterations "
            "and detect regression or plateau."
        )
    )
    parser.add_argument(
        "--scores-dir",
        required=True,
        help="Directory containing iterN/ subdirectories with scores.json files",
    )
    parser.add_argument(
        "--regression-threshold",
        type=float,
        default=-3.0,
        help=(
            "Minimum allowed per-dimension delta in the latest iteration. "
            "If any dimension drops more than this, trigger REGRESSION. "
            "(default: -3, i.e., flag if any dimension drops by more than 3 points)"
        ),
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional path to write a JSON report",
    )
    args = parser.parse_args()

    entries = load_scores(args.scores_dir)

    if not entries:
        print("[ERROR] No iterN/scores.json files found in scores-dir.", file=sys.stderr)
        sys.exit(1)

    if len(entries) == 1:
        print(f"Only one iteration found (iter{entries[0][0]}). No trajectory to analyze.")
        print_score_table(entries)
        if args.report_path:
            report = {
                "status": "ok",
                "latest_deltas": {},
                "history": [{"iter": entries[0][0], "scores": entries[0][1]}],
            }
            with open(args.report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        sys.exit(0)

    print_score_table(entries)

    # Analyze latest iteration for regression
    latest_idx = len(entries) - 1
    prev_scores = entries[latest_idx - 1][1]
    curr_scores = entries[latest_idx][1]
    latest_deltas = compute_deltas(prev_scores, curr_scores)
    latest_overall_delta = compute_overall(curr_scores) - compute_overall(prev_scores)

    # Check for REGRESSION in latest iteration
    regression_dims = [
        dim
        for dim, delta in latest_deltas.items()
        if delta < args.regression_threshold
    ]

    # Check for PLATEAU: overall delta < 1.0 for 2+ consecutive iterations
    plateau_count = 0
    for i in range(1, len(entries)):
        prev_overall = compute_overall(entries[i - 1][1])
        curr_overall = compute_overall(entries[i][1])
        if abs(curr_overall - prev_overall) < 1.0:
            plateau_count += 1
        else:
            plateau_count = 0  # reset on non-plateau iteration

    plateau_detected = plateau_count >= 2

    # Build history for report
    history = []
    for i, (iter_num, scores) in enumerate(entries):
        entry = {"iter": iter_num, "scores": scores, "overall": compute_overall(scores)}
        if i > 0:
            prev = entries[i - 1][1]
            entry["deltas"] = compute_deltas(prev, scores)
            entry["overall_delta"] = compute_overall(scores) - compute_overall(prev)
        history.append(entry)

    # Determine status
    status = "ok"
    exit_code = 0
    messages = []

    if regression_dims:
        status = "regression"
        exit_code = 1
        for dim in regression_dims:
            delta = latest_deltas[dim]
            messages.append(
                f"REGRESSION: {dim} dropped {delta:.1f} points in "
                f"iter{entries[latest_idx][0]} "
                f"(threshold: {args.regression_threshold})"
            )

    if plateau_detected and status == "ok":
        status = "plateau"
        exit_code = 1
        messages.append(
            f"PLATEAU: overall score change < 1.0 for {plateau_count} "
            f"consecutive iterations — further refinement unlikely to yield gains"
        )

    # Print status
    if messages:
        for msg in messages:
            print(f"[{status.upper()}] {msg}")
        print()
    else:
        print(f"[OK] No regression or plateau detected in latest iteration.")
        print(
            f"     Overall delta iter{entries[latest_idx-1][0]} → "
            f"iter{entries[latest_idx][0]}: "
            f"{latest_overall_delta:+.1f}"
        )

    # Write report if requested
    if args.report_path:
        report = {
            "status": status,
            "latest_deltas": latest_deltas,
            "history": history,
        }
        report_path = Path(args.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to: {args.report_path}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
