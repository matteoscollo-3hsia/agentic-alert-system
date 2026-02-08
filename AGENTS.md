# AGENTS

This repo contains the Agentic Alert System (CSV-driven pipeline, tests, and docs).
Use this file as the canonical operating guide for Codex work in this repo.

<!-- CODEX-TOOLKIT:START -->
## Codex Toolkit

### Scope and Guardrails
- Keep changes additive and isolated when adding tooling docs/scripts.
- Avoid modifying pipeline behavior unless explicitly requested.
- Prefer minimal diffs and document any non-obvious side effects.

### Codex Operating Guidelines
- Pinned threads: use a pinned thread for long-running work or multi-step reviews so context stays stable.
- Review panel inline comments: leave inline notes for risky changes or missing tests instead of broad summaries.
- Prevent sleep while running: keep the machine awake during long runs (use `caffeinate -dimsu` on macOS).

### Local Actions
- `uv sync`
- `uv run python -m agentic_alert.pipeline`
- `uv run pytest -q`
- `uv run pytest tests/unit/test_owner_import.py -q`
- `uv run python scripts/codex/update_agents_from_sessions.py --dry-run`

### Toolkit Update Script
- Script: `scripts/codex/update_agents_from_sessions.py`
- Purpose: scan `~/.codex/sessions` and propose minimal updates to this block.
- Safety: updates are confined to the markers below.

<!-- CODEX-TOOLKIT:AUTO:START -->
#### Session Notes (Auto)
- TODO: Review recent sessions for updates; no explicit AGENTS_NOTE found.
<!-- CODEX-TOOLKIT:AUTO:END -->

<!-- CODEX-TOOLKIT:END -->
