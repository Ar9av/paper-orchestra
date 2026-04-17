#!/usr/bin/env python3
"""
discover_logs.py — Phase 1 of agent-research-aggregator.

Scans known AI agent cache directories (.claude, .cursor, .antigravity,
.openclaw) plus general project files for experimentation logs.

Outputs a JSON manifest that downstream scripts and LLM calls use to decide
which files to read.

Usage:
    python discover_logs.py \\
        --search-roots . ~ \\
        --agents claude,cursor,antigravity,openclaw \\
        --depth 4 \\
        --since 2025-01-01 \\
        --out workspace/ara/discovered_logs.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config: per-agent directory names + file glob patterns
# ---------------------------------------------------------------------------

AGENT_SPECS = {
    "claude": {
        "cache_dirs": [".claude"],
        "global_dirs": [os.path.expanduser("~/.claude")],
        "patterns": [
            "memory/**/*.md",
            "projects/*/memory/**/*.md",
            "task-outputs/**/*.md",
            "task-outputs/**/*.txt",
            "todos/**/*.json",
        ],
        "root_files": ["CLAUDE.md"],
        "priority_dirs": ["memory"],
    },
    "cursor": {
        "cache_dirs": [".cursor"],
        "global_dirs": [
            os.path.expanduser("~/.cursor/User/globalStorage"),
        ],
        "patterns": [
            "chat/**/*.json",
            "chat/**/*.chat",
            "rules/**/*.md",
            "notes/**/*.md",
        ],
        "root_files": [".cursorrules"],
        "priority_dirs": ["chat"],
    },
    "antigravity": {
        "cache_dirs": [".antigravity"],
        "global_dirs": [],
        "patterns": [
            "workers/**/output.md",
            "workers/**/task.json",
            "workers/**/log.jsonl",
            "tasks/**/*.json",
            "task-registry.json",
        ],
        "root_files": [],
        "priority_dirs": ["workers"],
    },
    "openclaw": {
        "cache_dirs": [".openclaw"],
        "global_dirs": [],
        "patterns": [
            "sessions/**/conversation.md",
            "sessions/**/artifacts/**/*.json",
            "memory/**/*.md",
            "runs/**/stdout.log",
            "runs/**/metrics.json",
        ],
        "root_files": [],
        "priority_dirs": ["sessions", "memory"],
    },
}

# General project file patterns (agent-agnostic)
GENERAL_PATTERNS = [
    ("results*.json", "HIGH"),
    ("results*.csv", "HIGH"),
    ("results*.tsv", "HIGH"),
    ("experiments*.json", "HIGH"),
    ("experiments*.yaml", "HIGH"),
    ("metrics.json", "HIGH"),
    ("eval.json", "HIGH"),
    ("ablation*.md", "HIGH"),
    ("ablation*.json", "HIGH"),
    ("*.ipynb", "HIGH"),
    ("run_*.log", "HIGH"),
    ("train_*.log", "HIGH"),
    ("README.md", "MEDIUM"),
    ("notes*.md", "MEDIUM"),
    ("NOTES.md", "MEDIUM"),
    ("config*.yaml", "MEDIUM"),
    ("config*.json", "MEDIUM"),
    ("config*.toml", "MEDIUM"),
    ("*.log", "LOW"),
]

SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", ".tox", ".venv", "venv",
    "env", ".mypy_cache", ".pytest_cache", "dist", "build", "target",
    "site-packages", ".cargo",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".pem", ".key", ".p12", ".pfx", ".crt", ".cer",
    ".db", ".sqlite",  # SQLite noted separately; too risky to include wholesale
}

SKIP_NAMES = {
    ".env", ".env.local", ".env.production", "credentials.json",
    "secrets.json", "token.json",
}

MAX_FILE_BYTES = 200 * 1024  # 200 KB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(512)
        return b"\x00" in chunk
    except OSError:
        return True


def modified_after(path: Path, since: datetime | None) -> bool:
    if since is None:
        return True
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime >= since


def file_entry(path: Path, agent: str, priority: str, since: datetime | None) -> dict | None:
    """Build a manifest entry for a single file, or return None to skip."""
    if path.name in SKIP_NAMES:
        return None
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return None
    if not path.is_file():
        return None
    if is_binary(path):
        return None
    try:
        size = path.stat().st_size
        mtime = path.stat().st_mtime
    except OSError:
        return None
    if not modified_after(path, since):
        return None
    return {
        "path": str(path),
        "agent": agent,
        "priority": priority,
        "size_bytes": size,
        "modified_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
        "truncated": size > MAX_FILE_BYTES,
    }


def scan_dir_glob(base: Path, pattern: str, agent: str,
                  priority: str, depth: int, since: datetime | None) -> list[dict]:
    """Glob-expand a pattern relative to base, respecting depth and skip rules."""
    results = []
    try:
        for path in base.glob(pattern):
            # Depth check: count path components relative to base
            rel = path.relative_to(base)
            if len(rel.parts) > depth:
                continue
            # Skip known junk directories anywhere in the path
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            entry = file_entry(path, agent, priority, since)
            if entry:
                results.append(entry)
    except (PermissionError, OSError):
        pass
    return results


def scan_root_files(base: Path, names: list[str], agent: str,
                    since: datetime | None) -> list[dict]:
    results = []
    for name in names:
        path = base / name
        entry = file_entry(path, agent, "HIGH", since)
        if entry:
            results.append(entry)
    return results


def scan_general(base: Path, depth: int, since: datetime | None) -> list[dict]:
    results = []
    for pattern, priority in GENERAL_PATTERNS:
        try:
            for path in base.glob(pattern):
                rel = path.relative_to(base)
                if len(rel.parts) > depth:
                    continue
                if any(part in SKIP_DIRS for part in rel.parts):
                    continue
                entry = file_entry(path, "general", priority, since)
                if entry:
                    results.append(entry)
        except (PermissionError, OSError):
            pass
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def decode_claude_project_path(dir_name: str) -> str | None:
    """
    Claude Code encodes project paths as directory names by replacing '/' with '-'.
    e.g. '-home-user-projects-myproject' → '/home/user/projects/myproject'
    Returns None if it doesn't look like an encoded path.
    """
    if not dir_name.startswith("-"):
        return None
    # Replace leading '-' then swap remaining '-' that correspond to path separators.
    # The heuristic: a segment starting with '-' followed by a lowercase letter or
    # digit is likely an encoded absolute path.
    decoded = dir_name.replace("-", "/")
    if decoded.startswith("/") and len(decoded) > 2:
        return decoded
    return None


def infer_project(path: Path, search_root: Path, agent: str) -> str:
    """
    Infer a human-readable project label for a file.

    For Claude Code logs stored under ~/.claude/projects/<encoded-path>/,
    decode the project directory name back to the original path.
    For all other files, use the search root name or a top-level subdirectory.
    """
    try:
        rel = path.relative_to(Path.home() / ".claude" / "projects")
        top = rel.parts[0] if rel.parts else ""
        decoded = decode_claude_project_path(top)
        if decoded:
            return decoded
    except ValueError:
        pass

    # For files inside a search root, use the root itself as the project label
    try:
        path.relative_to(search_root)
        return str(search_root)
    except ValueError:
        pass

    return str(path.parent)


def main():
    parser = argparse.ArgumentParser(description="Discover AI agent experiment logs")
    parser.add_argument("--search-roots", default=".", help="Comma-separated root dirs to scan")
    parser.add_argument("--agents", default="claude,cursor,antigravity,openclaw",
                        help="Comma-separated agent types to scan")
    parser.add_argument("--depth", type=int, default=4, help="Max directory depth")
    parser.add_argument("--since", default=None,
                        help="ISO 8601 date; only include files modified after this")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--project", default=None,
                        help="Filter to files belonging to this project label only "
                             "(must match a label from a prior discovery run)")
    args = parser.parse_args()

    search_roots = [Path(r.strip()).expanduser().resolve()
                    for r in args.search_roots.split(",")]
    enabled_agents = [a.strip() for a in args.agents.split(",")]
    since_dt: datetime | None = None
    if args.since:
        since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)

    all_entries: list[dict] = []
    agent_counts: dict[str, int] = {}

    for root in search_roots:
        if not root.exists():
            print(f"[WARN] search root does not exist: {root}", file=sys.stderr)
            continue

        # --- Agent-specific scans ---
        for agent, spec in AGENT_SPECS.items():
            if agent not in enabled_agents:
                continue
            agent_counts.setdefault(agent, 0)

            dirs_to_scan: list[Path] = []
            for cache_dir in spec["cache_dirs"]:
                candidate = root / cache_dir
                if candidate.exists():
                    dirs_to_scan.append(candidate)
            for global_dir in spec["global_dirs"]:
                candidate = Path(global_dir)
                if candidate.exists():
                    dirs_to_scan.append(candidate)

            for base in dirs_to_scan:
                for pattern in spec["patterns"]:
                    priority = "HIGH" if any(
                        p in pattern for p in spec.get("priority_dirs", [])
                    ) else "MEDIUM"
                    entries = scan_dir_glob(base, pattern, agent, priority,
                                            args.depth, since_dt)
                    for e in entries:
                        e["project"] = infer_project(Path(e["path"]), root, agent)
                    all_entries.extend(entries)
                    agent_counts[agent] += len(entries)

            # Root-level files (e.g. CLAUDE.md, .cursorrules)
            entries = scan_root_files(root, spec["root_files"], agent, since_dt)
            for e in entries:
                e["project"] = infer_project(Path(e["path"]), root, agent)
            all_entries.extend(entries)
            agent_counts[agent] += len(entries)

        # --- General project file scan ---
        entries = scan_general(root, args.depth, since_dt)
        for e in entries:
            e["project"] = infer_project(Path(e["path"]), root, "general")
        all_entries.extend(entries)
        agent_counts["general"] = agent_counts.get("general", 0) + len(entries)

    # Deduplicate by path (a file might match multiple patterns)
    seen_paths: set[str] = set()
    deduped: list[dict] = []
    for e in all_entries:
        if e["path"] not in seen_paths:
            seen_paths.add(e["path"])
            deduped.append(e)

    # Sort: HIGH > MEDIUM > LOW, then by modified desc
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    deduped.sort(key=lambda e: (priority_order.get(e["priority"], 9),
                                 -Path(e["path"]).stat().st_mtime
                                 if Path(e["path"]).exists() else 0))

    # Build project → file list index (before optional filtering)
    by_project: dict[str, list[str]] = {}
    for e in deduped:
        proj = e.get("project", "unknown")
        by_project.setdefault(proj, []).append(e["path"])

    # Apply --project filter if requested
    if args.project:
        filtered = [e for e in deduped if e.get("project") == args.project]
        if not filtered:
            print(f"[ERROR] No files matched project '{args.project}'.", file=sys.stderr)
            print("Available projects:", file=sys.stderr)
            for proj in sorted(by_project):
                print(f"  {proj}", file=sys.stderr)
            sys.exit(1)
        deduped = filtered

    # Build output manifest
    manifest = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "search_roots": [str(r) for r in search_roots],
        "agents_scanned": enabled_agents,
        "since": args.since,
        "depth": args.depth,
        "selected_project": args.project,
        "total_files": len(deduped),
        "total_size_bytes": sum(e["size_bytes"] for e in deduped),
        "by_agent": agent_counts,
        "by_project": {p: len(paths) for p, paths in by_project.items()},
        "files": deduped,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Human-readable summary to stdout
    print(f"\n=== Agent Log Discovery Summary ===")
    print(f"Search roots : {', '.join(str(r) for r in search_roots)}")
    print(f"Agents       : {', '.join(enabled_agents)}")
    print(f"Depth        : {args.depth}")
    print(f"Since        : {args.since or 'all time'}")
    print()

    # Always show the project list — this is the key output for project selection
    print("Projects found:")
    for i, (proj, paths) in enumerate(sorted(by_project.items()), 1):
        marker = " ◀ selected" if args.project and proj == args.project else ""
        print(f"  [{i}] {proj}  ({len(paths)} files){marker}")
    print()

    if args.project:
        print(f"Filtered to project: {args.project}")
    else:
        print("[ACTION REQUIRED] Select a project before proceeding to Phase 2.")
        print("Re-run with --project <label> to filter to one project.")
    print()

    print(f"Total files  : {len(deduped)}")
    print(f"Total size   : {sum(e['size_bytes'] for e in deduped) / 1024:.1f} KB")
    print()
    print("By agent:")
    for agent, count in sorted(agent_counts.items()):
        print(f"  {agent:20s} {count:4d} files")
    print()
    print("Priority breakdown:")
    for prio in ("HIGH", "MEDIUM", "LOW"):
        n = sum(1 for e in deduped if e["priority"] == prio)
        print(f"  {prio:8s} {n:4d} files")
    truncated = [e for e in deduped if e.get("truncated")]
    if truncated:
        print(f"\n[WARN] {len(truncated)} file(s) exceed 200 KB and will be truncated:")
        for e in truncated[:5]:
            print(f"  {e['path']} ({e['size_bytes']//1024} KB)")
        if len(truncated) > 5:
            print(f"  ... and {len(truncated)-5} more")
    print(f"\nManifest written to: {args.out}")
    if not args.project:
        # Exit with code 2 to signal to the caller that project selection is needed
        sys.exit(2)
    if len(deduped) > 50:
        print(f"\n[ACTION REQUIRED] {len(deduped)} files found — review the manifest")
        print("and confirm with the user before proceeding to Phase 2.")


if __name__ == "__main__":
    main()
