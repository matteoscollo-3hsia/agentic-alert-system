#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

CODEX_START = "<!-- CODEX-TOOLKIT:START -->"
CODEX_END = "<!-- CODEX-TOOLKIT:END -->"
AUTO_START = "<!-- CODEX-TOOLKIT:AUTO:START -->"
AUTO_END = "<!-- CODEX-TOOLKIT:AUTO:END -->"


@dataclass
class SkillSuggestion:
    name: str
    description: str
    source: str


def _session_root() -> Path:
    return Path.home() / ".codex" / "sessions"


def _iter_session_files(
    root: Path, days: int | None, max_files: int | None
) -> list[Path]:
    if not root.exists():
        return []

    files = [path for path in root.rglob("*") if path.is_file()]
    if days is not None and days > 0:
        cutoff = datetime.now().timestamp() - timedelta(days=days).total_seconds()
        files = [path for path in files if path.stat().st_mtime >= cutoff]

    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    if max_files is not None and max_files > 0:
        files = files[:max_files]

    return files


def _dedupe_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _parse_skill_payload(payload: str) -> tuple[str, str]:
    if ":" in payload:
        name, desc = payload.split(":", 1)
        return name.strip(), desc.strip()
    if " - " in payload:
        name, desc = payload.split(" - ", 1)
        return name.strip(), desc.strip()
    return payload.strip(), ""


def collect_session_updates(
    session_files: list[Path],
) -> tuple[list[str], list[str], list[SkillSuggestion]]:
    notes: list[str] = []
    todos: list[str] = []
    skills: list[SkillSuggestion] = []

    note_pattern = re.compile(r"^\s*AGENTS_NOTE:\s*(.+)$")
    todo_pattern = re.compile(r"^\s*AGENTS_TODO:\s*(.+)$")
    skill_pattern = re.compile(r"^\s*SKILL_SUGGESTION:\s*(.+)$")

    for path in session_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line in content.splitlines():
            match = note_pattern.match(line)
            if match:
                payload = match.group(1).strip()
                if payload:
                    notes.append(f"{payload} (source: {path.name})")
                continue
            match = todo_pattern.match(line)
            if match:
                payload = match.group(1).strip()
                if payload:
                    todos.append(f"{payload} (source: {path.name})")
                continue
            match = skill_pattern.match(line)
            if match:
                payload = match.group(1).strip()
                if payload:
                    name, desc = _parse_skill_payload(payload)
                    if name:
                        skills.append(
                            SkillSuggestion(
                                name=name,
                                description=desc,
                                source=path.name,
                            )
                        )

    return _dedupe_preserve(notes), _dedupe_preserve(todos), skills


def render_auto_section(notes: list[str], todos: list[str]) -> str:
    if not notes and not todos:
        todos = [
            "Review recent sessions for updates; no explicit AGENTS_NOTE found."
        ]

    lines = [AUTO_START, "#### Session Notes (Auto)"]
    for note in notes:
        lines.append(f"- {note}")
    for todo in todos:
        if todo.lower().startswith("todo:"):
            lines.append(f"- {todo}")
        else:
            lines.append(f"- TODO: {todo}")
    lines.append(AUTO_END)
    return "\n".join(lines)


def _split_marked(text: str) -> tuple[str, str, str]:
    start = text.find(CODEX_START)
    end = text.find(CODEX_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("Missing CODEX-TOOLKIT markers in AGENTS.md")
    end += len(CODEX_END)
    return text[:start], text[start:end], text[end:]


def update_agents_content(text: str, auto_section: str) -> str:
    prefix, marked, suffix = _split_marked(text)

    if AUTO_START in marked and AUTO_END in marked:
        auto_start = marked.find(AUTO_START)
        auto_end = marked.find(AUTO_END)
        auto_end += len(AUTO_END)
        updated_marked = marked[:auto_start] + auto_section + marked[auto_end:]
    else:
        insert_at = marked.rfind(CODEX_END)
        before = marked[:insert_at].rstrip()
        updated_marked = f"{before}\n\n{auto_section}\n\n{marked[insert_at:]}"

    updated = prefix + updated_marked + suffix

    if not updated.startswith(prefix) or not updated.endswith(suffix):
        raise RuntimeError("Update would modify content outside CODEX markers")

    return updated


def _slugify(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in name.lower())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "skill"


def _write_skill_file(
    suggestion: SkillSuggestion,
    skills_root: Path,
    force: bool,
) -> Path:
    skills_root.mkdir(parents=True, exist_ok=True)
    base = _slugify(suggestion.name)
    target = skills_root / f"{base}.md"

    if target.exists() and not force:
        counter = 2
        while True:
            candidate = skills_root / f"{base}_v{counter}.md"
            if not candidate.exists():
                target = candidate
                break
            counter += 1

    content_lines = [
        f"# {suggestion.name}",
        "",
        suggestion.description or "TODO: Add skill description.",
        "",
        f"Source: {suggestion.source}",
    ]
    target.write_text("\n".join(content_lines) + "\n", encoding="utf-8")
    return target


def _print_diff(original: str, updated: str) -> None:
    diff = difflib.unified_diff(
        original.splitlines(),
        updated.splitlines(),
        fromfile="AGENTS.md",
        tofile="AGENTS.md (updated)",
        lineterm="",
    )
    print("\n".join(diff))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update AGENTS.md from Codex sessions"
    )
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--agents-path",
        default="AGENTS.md",
        help="Path to AGENTS.md",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        args.dry_run = True

    sessions_root = _session_root()
    if not sessions_root.exists():
        print(f"No sessions found at {sessions_root}. Nothing to update.")
        return 0

    session_files = _iter_session_files(
        sessions_root, args.days, args.max_files
    )
    if not session_files:
        print("No session files matched the criteria. Nothing to update.")
        return 0

    notes, todos, skills = collect_session_updates(session_files)
    auto_section = render_auto_section(notes, todos)

    agents_path = Path(args.agents_path)
    if not agents_path.exists():
        print(f"AGENTS file not found at {agents_path}")
        return 1

    original = agents_path.read_text(encoding="utf-8")
    updated = update_agents_content(original, auto_section)

    if original == updated:
        print("AGENTS.md unchanged.")
    elif args.dry_run:
        _print_diff(original, updated)
    if args.apply and original != updated:
        agents_path.write_text(updated, encoding="utf-8")
        print("AGENTS.md updated.")

    if skills and not args.apply:
        print(
            f"Found {len(skills)} skill suggestion(s). "
            "Re-run with --apply to write skill files."
        )

    if skills and args.apply:
        skills_root = Path("skills") / "codex"
        for suggestion in skills:
            target = _write_skill_file(
                suggestion, skills_root, force=args.force
            )
            print(f"Skill file written: {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
