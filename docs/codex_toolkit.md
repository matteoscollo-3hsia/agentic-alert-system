# Codex Toolkit

This document describes the lightweight Codex tooling layer added to the repo.

## Overview
- `AGENTS.md` is the canonical guide for Codex operations in this repo.
- Automated updates are confined to the `<!-- CODEX-TOOLKIT:START -->` ... `<!-- CODEX-TOOLKIT:END -->` block.
- Session-derived updates are inserted only inside the auto sub-block:
  `<!-- CODEX-TOOLKIT:AUTO:START -->` ... `<!-- CODEX-TOOLKIT:AUTO:END -->`.

## Update Script
Script: `scripts/codex/update_agents_from_sessions.py`

Usage examples:
```bash
uv run python scripts/codex/update_agents_from_sessions.py --dry-run
uv run python scripts/codex/update_agents_from_sessions.py --days 7 --max-files 200 --dry-run
uv run python scripts/codex/update_agents_from_sessions.py --apply
```

Behavior:
- Scans `~/.codex/sessions` recursively.
- Extracts `AGENTS_NOTE:` / `AGENTS_TODO:` lines for minimal updates.
- If no explicit notes are found, it adds a short TODO instead of inventing guidance.
- Optionally proposes new skills under `skills/codex/` when `SKILL_SUGGESTION:` lines appear.

## Skill Suggestions
To suggest a new repo-local skill, add a line in a session file like:
```
SKILL_SUGGESTION: rss-debugging: Workflow for diagnosing RSS feed failures
```
The script will create `skills/codex/rss-debugging.md` unless it already exists.
Without `--force`, it never overwrites existing skill files.
