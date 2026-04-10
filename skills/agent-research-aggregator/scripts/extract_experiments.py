#!/usr/bin/env python3
"""
extract_experiments.py — Phase 2 helper for agent-research-aggregator.

This script has two modes:

1. BATCH MODE (called by the host agent to prepare batches):
   Reads discovered_logs.json, groups files into batches under a size budget,
   and prints the list of file paths per batch so the host LLM knows what to
   read and extract.

   python extract_experiments.py \\
       --discovered workspace/ara/discovered_logs.json \\
       --list-batches \\
       --batch-bytes 40000

2. VALIDATE MODE (called after host has done all LLM extraction calls):
   Reads raw_experiments.json produced by the host and validates it meets
   the minimum schema before Phase 3.

   python extract_experiments.py \\
       --discovered workspace/ara/discovered_logs.json \\
       --out workspace/ara/raw_experiments.json \\
       --validate-only

Usage for validate mode:
    python extract_experiments.py \\
        --out workspace/ara/raw_experiments.json \\
        --validate-only
"""

import argparse
import json
import sys
from pathlib import Path


REQUIRED_TOP_KEYS = {"experiments"}
EXPERIMENT_REQUIRED = {"experiment_id", "confidence"}
EXPERIMENT_ONE_OF = {"hypothesis", "method", "results", "research_question"}

VALID_CONFIDENCE = {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# Batch listing (for host agent to know what to read)
# ---------------------------------------------------------------------------

def list_batches(discovered_path: str, batch_bytes: int):
    with open(discovered_path, encoding="utf-8") as f:
        manifest = json.load(f)

    files = manifest.get("files", [])
    if not files:
        print("No files in manifest.", file=sys.stderr)
        sys.exit(1)

    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_size = 0

    for entry in files:
        size = min(entry["size_bytes"], 200 * 1024)  # cap at truncation limit
        if current_batch and current_size + size > batch_bytes:
            batches.append(current_batch)
            current_batch = []
            current_size = 0
        current_batch.append(entry)
        current_size += size

    if current_batch:
        batches.append(current_batch)

    print(f"Total batches: {len(batches)}")
    print(f"Total files  : {len(files)}")
    print()
    for i, batch in enumerate(batches, 1):
        total = sum(min(e["size_bytes"], 200*1024) for e in batch)
        print(f"--- Batch {i} ({len(batch)} files, ~{total//1024} KB) ---")
        for entry in batch:
            trunc = " [TRUNCATED]" if entry.get("truncated") else ""
            print(f"  [{entry['priority']:6}] [{entry['agent']:12}] {entry['path']}{trunc}")
        print()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_experiments(out_path: str) -> bool:
    path = Path(out_path)
    if not path.exists():
        print(f"[ERROR] File not found: {out_path}", file=sys.stderr)
        return False

    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        return False

    # Top-level structure
    missing_top = REQUIRED_TOP_KEYS - set(data.keys())
    if missing_top:
        print(f"[ERROR] Missing top-level keys: {missing_top}", file=sys.stderr)
        return False

    experiments = data["experiments"]
    if not isinstance(experiments, list):
        print("[ERROR] 'experiments' must be a list", file=sys.stderr)
        return False

    if len(experiments) == 0:
        print("[WARN] 'experiments' array is empty — no extractable data found.")
        print("This may be correct if logs contained no experiment data.")
        print("Proceeding to Phase 3 with empty input is allowed but will")
        print("produce a synthesis with no results — confirm with user.")

    errors = []
    warnings = []

    for i, exp in enumerate(experiments):
        label = exp.get("experiment_id", f"[index {i}]")

        # Required keys
        for key in EXPERIMENT_REQUIRED:
            if key not in exp:
                errors.append(f"{label}: missing required key '{key}'")

        # At least one of these must be present
        if not any(k in exp for k in EXPERIMENT_ONE_OF):
            errors.append(f"{label}: must have at least one of {EXPERIMENT_ONE_OF}")

        # Confidence value
        conf = exp.get("confidence", "")
        if conf not in VALID_CONFIDENCE:
            errors.append(f"{label}: 'confidence' must be one of {VALID_CONFIDENCE}, got '{conf}'")

        # Results tables shape
        results = exp.get("results", {})
        if isinstance(results, dict):
            for j, table in enumerate(results.get("tables", [])):
                if not isinstance(table.get("headers"), list):
                    errors.append(f"{label}: results.tables[{j}].headers must be a list")
                if not isinstance(table.get("rows"), list):
                    errors.append(f"{label}: results.tables[{j}].rows must be a list")

        # Warn about low-confidence experiments with no numeric data
        if conf == "low":
            key_nums = results.get("key_numbers", []) if isinstance(results, dict) else []
            tables = results.get("tables", []) if isinstance(results, dict) else []
            if not key_nums and not tables:
                warnings.append(f"{label}: low confidence + no numeric data")

    for w in warnings:
        print(f"[WARN] {w}")

    if errors:
        for e in errors:
            print(f"[ERROR] {e}", file=sys.stderr)
        print(f"\nValidation FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return False

    print(f"Validation PASSED: {len(experiments)} experiment(s), {len(warnings)} warning(s)")
    high = sum(1 for e in experiments if e.get("confidence") == "high")
    med  = sum(1 for e in experiments if e.get("confidence") == "medium")
    low  = sum(1 for e in experiments if e.get("confidence") == "low")
    print(f"  Confidence: {high} high / {med} medium / {low} low")
    tables_total = sum(
        len(e.get("results", {}).get("tables", []))
        for e in experiments if isinstance(e.get("results"), dict)
    )
    print(f"  Result tables found: {tables_total}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase 2 helper: batch listing and validation")
    parser.add_argument("--discovered", default=None,
                        help="Path to discovered_logs.json (required for --list-batches)")
    parser.add_argument("--out", default=None,
                        help="Path to raw_experiments.json (required for --validate-only)")
    parser.add_argument("--list-batches", action="store_true",
                        help="Print batches of files for the host agent to process")
    parser.add_argument("--batch-bytes", type=int, default=40000,
                        help="Soft byte budget per LLM extraction batch (default: 40000)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Validate raw_experiments.json (requires --out)")
    args = parser.parse_args()

    if args.list_batches:
        if not args.discovered:
            print("[ERROR] --list-batches requires --discovered", file=sys.stderr)
            sys.exit(1)
        list_batches(args.discovered, args.batch_bytes)
        sys.exit(0)

    if args.validate_only:
        if not args.out:
            print("[ERROR] --validate-only requires --out", file=sys.stderr)
            sys.exit(1)
        ok = validate_experiments(args.out)
        sys.exit(0 if ok else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
