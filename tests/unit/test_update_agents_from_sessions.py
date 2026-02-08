import importlib.util
import sys
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "scripts" / "codex" / "update_agents_from_sessions.py"
    spec = importlib.util.spec_from_file_location(
        "update_agents_from_sessions", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collects_notes_and_updates_only_marked_block(tmp_path: Path) -> None:
    module = _load_module()

    session_file = tmp_path / "session.log"
    session_file.write_text(
        "AGENTS_NOTE: Prefer local RSS for smoke tests\n",
        encoding="utf-8",
    )

    notes, todos, _skills = module.collect_session_updates([session_file])
    auto_section = module.render_auto_section(notes, todos)

    original = (
        "Intro\n"
        f"{module.CODEX_START}\n"
        "Manual content\n"
        f"{module.AUTO_START}\n"
        "Old note\n"
        f"{module.AUTO_END}\n"
        f"{module.CODEX_END}\n"
        "Outro\n"
    )

    updated = module.update_agents_content(original, auto_section)

    assert "Prefer local RSS for smoke tests" in updated
    assert updated.startswith("Intro\n")
    assert updated.endswith("Outro\n")


def test_inserts_auto_block_when_missing(tmp_path: Path) -> None:
    module = _load_module()

    session_file = tmp_path / "session.log"
    session_file.write_text(
        "AGENTS_TODO: Add review checklist\n",
        encoding="utf-8",
    )

    notes, todos, _skills = module.collect_session_updates([session_file])
    auto_section = module.render_auto_section(notes, todos)

    original = (
        "Header\n"
        f"{module.CODEX_START}\n"
        "Manual only\n"
        f"{module.CODEX_END}\n"
        "Footer\n"
    )

    updated = module.update_agents_content(original, auto_section)

    assert module.AUTO_START in updated
    assert "Add review checklist" in updated
    assert updated.startswith("Header\n")
    assert updated.endswith("Footer\n")
