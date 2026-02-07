import csv
import shutil
from pathlib import Path

from agentic_alert.pipeline import run_daily


def _copy_data_files(repo_root: Path, destination: Path) -> None:
    data_dir = repo_root / "data"
    files = [
        "companies.csv",
        "triggers.csv",
        "providers.csv",
        "articles.csv",
    ]
    for filename in files:
        shutil.copy(data_dir / filename, destination / filename)


def _count_alert_rows(path: Path) -> int:
    if not path.exists():
        return 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def test_pipeline_generates_alerts_no_dupes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    _copy_data_files(repo_root, tmp_path)

    monkeypatch.setenv("COMPANIES_CSV", str(tmp_path / "companies.csv"))
    monkeypatch.setenv("TRIGGERS_CSV", str(tmp_path / "triggers.csv"))
    monkeypatch.setenv("PROVIDERS_CSV", str(tmp_path / "providers.csv"))
    monkeypatch.setenv("ARTICLES_CSV", str(tmp_path / "articles.csv"))
    monkeypatch.setenv("ALERTS_CSV", str(tmp_path / "alerts.csv"))
    monkeypatch.setenv(
        "ALERT_CANDIDATES_CSV", str(tmp_path / "alert_candidates.csv")
    )
    monkeypatch.setenv("ALERTS_ENABLED", "false")

    run_daily()
    output = capsys.readouterr().out
    expected_path = str((tmp_path / "companies.csv").resolve())
    assert f"Using companies_csv: {expected_path}" in output
    first_count = _count_alert_rows(tmp_path / "alerts.csv")

    run_daily()
    second_count = _count_alert_rows(tmp_path / "alerts.csv")

    assert first_count > 0
    assert second_count == first_count
