import csv
from pathlib import Path

from agentic_alert.config import AppConfig
from agentic_alert.pipeline import _run_pipeline


def _write_csv(path: Path, header: str, rows: list[str]) -> None:
    path.write_text(
        header + "\n" + "\n".join(rows) + "\n", encoding="utf-8"
    )


def test_backtest_writes_alerts_and_dedupe(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    companies_csv = data_dir / "companies.csv"
    triggers_csv = data_dir / "triggers.csv"
    providers_csv = data_dir / "providers.csv"
    articles_csv = data_dir / "articles.csv"
    alerts_backtest_csv = data_dir / "alerts_backtest.csv"

    _write_csv(
        companies_csv,
        "company_id,name,aliases,revenue_eur,industry_code,industry_description,"
        "website,website_domain,country,contact_owner,status",
        [
            "c001,Alpha Energia,Alpha Energia S.p.A.;Alpha Energia Italia,"
            "100000000,3510,Energy,https://www.alphaenergia.it,alphaenergia.it,"
            "IT,info@alphaenergia.it,active"
        ],
    )

    _write_csv(
        triggers_csv,
        "trigger_id,name,keywords,priority,description",
        ["t001,Acquisizione,acquisizione;merger,high,Deal trigger"],
    )

    _write_csv(
        providers_csv,
        "provider_id,name,type,base_url,enabled",
        ["p001,Local Dummy,dummy,,true"],
    )

    _write_csv(
        articles_csv,
        "article_id,provider_id,source_name,title,url,published_at,content_snippet",
        [
            "a001,p001,Local Dummy,Acquisizione di Alpha Energia,"
            "https://example.com/a,2026-02-01T00:00:00+00:00,"
            "Alpha Energia Italia annuncia un'acquisizione"
        ],
    )

    config = AppConfig(
        companies_csv=companies_csv,
        triggers_csv=triggers_csv,
        providers_csv=providers_csv,
        articles_csv=articles_csv,
        rss_snapshot_path=data_dir / "sample.xml",
        alert_candidates_csv=data_dir / "alert_candidates.csv",
        alerts_csv=data_dir / "alerts.csv",
        backtest_output_csv=alerts_backtest_csv,
        alerts_enabled=False,
        alert_channel="slack",
        slack_webhook_url="",
        backtest_enabled=True,
        backtest_lookback_days=7,
        backtest_company_ids="c001",
    )

    _run_pipeline(config)
    _run_pipeline(config)

    with alerts_backtest_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames is not None
    assert "run_type" in reader.fieldnames
    assert len(rows) == 1
    assert rows[0]["run_type"] == "backtest"
