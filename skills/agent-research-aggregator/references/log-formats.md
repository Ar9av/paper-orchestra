# Agent Log Formats

Reference for `discover_logs.py`. Describes what each agent type stores and
which files are most likely to contain experiment data.

---

## Claude Code (`.claude/`)

Claude Code stores all persistent state under `.claude/` at the project root
(or `~/.claude/` for global state).

### Memory files — HIGH VALUE

```
.claude/projects/<workspace-hash>/memory/
    *.md          # Structured memory entries (frontmatter: name, description, type)
~/.claude/projects/<workspace-hash>/memory/
    *.md          # Same, global location
```

Memory files use this frontmatter schema:
```yaml
---
name: <title>
description: <one-line hook>
type: user | feedback | project | reference
---
```

Types to prioritize:
- `type: project` — contains experiment goals, decisions, blockers
- `type: feedback` — contains "what worked / what didn't" patterns
- `type: user` — background context (role, domain knowledge)
- `type: reference` — external links + dataset/codebase pointers

### CLAUDE.md — HIGH VALUE

```
CLAUDE.md                   # Project-level instructions
.claude/CLAUDE.md           # Alternative location
```

Often contains: project description, experimental context, constraints,
design decisions that inform the research framing.

### Task outputs — MEDIUM VALUE

Claude Code task outputs (from the `TaskOutput` tool) may appear as:
```
.claude/task-outputs/
    *.md
    *.txt
```

These contain agent responses to long-running tasks — may include benchmark
runs, code generation results, test outputs.

### Todos — LOW VALUE (structure only)

```
.claude/todos/
    *.json        # {id, content, status, priority}
```

Useful for understanding what experiments were planned vs. completed.

---

## Cursor (`.cursor/`)

Cursor stores workspace AI data under `.cursor/` at the project root.

### Chat history — HIGH VALUE

```
.cursor/chat/
    chatHistory.json        # Array of {role, content, timestamp} objects
    *.chat                  # Per-session chat files (same format)
```

Also check SQLite databases:
```
~/.cursor/User/globalStorage/
    *.db                    # SQLite; table `ItemTable` has key-value chat data
```

SQLite query: `SELECT value FROM ItemTable WHERE key LIKE '%chat%'`

### Rules — MEDIUM VALUE

```
.cursor/rules/
    *.md                    # Cursor rules (may describe project + constraints)
.cursorrules                # Root-level rules file
```

### Notes / scratchpad — MEDIUM VALUE

```
.cursor/notes/
    *.md
```

---

## Antigravity (`.antigravity/`)

Antigravity is a multi-worker coding agent. Stores per-task logs and
worker outputs.

### Worker logs — HIGH VALUE

```
.antigravity/workers/
    <worker-id>/
        log.jsonl           # Newline-delimited JSON events
        output.md           # Final worker output
        task.json           # Task specification
```

Each `log.jsonl` line:
```json
{"ts": "ISO-8601", "type": "tool_result|message|error", "content": "..."}
```

### Task registry — MEDIUM VALUE

```
.antigravity/tasks/
    <task-id>.json          # {id, description, status, created_at, outputs[]}
.antigravity/task-registry.json   # Index of all tasks
```

### Workspace snapshots — LOW VALUE (size risk)

```
.antigravity/snapshots/
    <snapshot-id>/          # Git-bundle or diff snapshots between runs
```

Skip these unless `--include-snapshots` is passed (not default).

---

## OpenClaw (`.openclaw/`)

OpenClaw follows a similar structure to Claude Code but uses different
file names.

### Session logs — HIGH VALUE

```
.openclaw/sessions/
    <session-id>/
        conversation.md     # Full conversation in markdown
        artifacts/
            *.py, *.json    # Generated code + data files
```

### Memory — HIGH VALUE

```
.openclaw/memory/
    *.md                    # Structured notes (same frontmatter as Claude Code)
```

### Run outputs — MEDIUM VALUE

```
.openclaw/runs/
    <run-id>/
        stdout.log
        stderr.log
        exit_code.txt
        metrics.json        # Agent-emitted key-value metrics
```

---

## General project files (scanned regardless of agent)

These are scanned in the project root and common subdirectory names regardless
of which agent produced them:

| Pattern | Priority | Rationale |
|---|---|---|
| `results*.{json,csv,tsv}` | HIGH | Likely benchmark output |
| `experiments*.{json,yaml}` | HIGH | Experiment configs + results |
| `*.ipynb` | HIGH | Jupyter notebooks with outputs |
| `run_*.log`, `train_*.log` | HIGH | Training/eval logs |
| `metrics.json`, `eval.json` | HIGH | Structured metric files |
| `ablation*.{md,json}` | HIGH | Ablation study data |
| `README.md` (root only) | MEDIUM | Often summarizes experiments |
| `notes*.md`, `NOTES.md` | MEDIUM | Researcher notes |
| `config*.{yaml,json,toml}` | MEDIUM | Hyperparameter configs |
| `*.log` (root level) | LOW | Generic logs; scan headers only |

**Skip always:**
- `node_modules/`, `.git/`, `__pycache__/`, `*.pyc`
- Files > 200 KB (note path in report but don't read)
- Binary files (check magic bytes: `\x00` in first 512 bytes)
- Credential-like files: `*.pem`, `*.key`, `.env`, `credentials*`

---

## Extraction priority ranking

When logs exceed the batch size budget, process in this order:

1. Memory files (`.claude/memory/`, `.openclaw/memory/`)
2. Chat history / conversation logs with tool outputs
3. `metrics.json`, `eval.json`, structured result files
4. Jupyter notebooks (`.ipynb`)
5. Training logs (`run_*.log`, `train_*.log`)
6. CLAUDE.md / `.cursorrules` / project notes
7. Task specifications and todos
8. Generic README / notes files
