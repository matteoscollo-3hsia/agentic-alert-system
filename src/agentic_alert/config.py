import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    companies_csv: Path = Path("data/companies.csv")
    triggers_csv: Path = Path("data/triggers.csv")
    providers_csv: Path = Path("data/providers.csv")
    articles_csv: Path = Path("data/articles.csv")
    rss_snapshot_path: Path = Path("data/rss_snapshots/sample.xml")
    alert_candidates_csv: Path = Path("data/alert_candidates.csv")
    alerts_csv: Path = Path("data/alerts.csv")
    backtest_output_csv: Path = Path("data/alerts_backtest.csv")
    alerts_enabled: bool = False
    alert_channel: str = "tbd"
    slack_webhook_url: str = ""
    backtest_enabled: bool = False
    backtest_lookback_days: int = 14
    backtest_company_ids: str = ""


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    return Path(value)


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    logger.warning("Invalid boolean value for %s: %s", name, value)
    return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer value for %s: %s", name, value)
        return default


def load_config() -> AppConfig:
    """Load configuration from defaults and optional .env overrides."""
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)

    defaults = AppConfig()

    return AppConfig(
        companies_csv=_env_path("COMPANIES_CSV", defaults.companies_csv),
        triggers_csv=_env_path("TRIGGERS_CSV", defaults.triggers_csv),
        providers_csv=_env_path("PROVIDERS_CSV", defaults.providers_csv),
        articles_csv=_env_path("ARTICLES_CSV", defaults.articles_csv),
        rss_snapshot_path=_env_path(
            "RSS_SNAPSHOT_PATH", defaults.rss_snapshot_path
        ),
        alert_candidates_csv=_env_path(
            "ALERT_CANDIDATES_CSV", defaults.alert_candidates_csv
        ),
        alerts_csv=_env_path("ALERTS_CSV", defaults.alerts_csv),
        backtest_output_csv=_env_path(
            "BACKTEST_OUTPUT_CSV", defaults.backtest_output_csv
        ),
        alerts_enabled=_env_bool("ALERTS_ENABLED", defaults.alerts_enabled),
        alert_channel=_env_str("ALERT_CHANNEL", defaults.alert_channel),
        slack_webhook_url=_env_str(
            "SLACK_WEBHOOK_URL", defaults.slack_webhook_url
        ),
        backtest_enabled=_env_bool(
            "BACKTEST_ENABLED", defaults.backtest_enabled
        ),
        backtest_lookback_days=_env_int(
            "BACKTEST_LOOKBACK_DAYS", defaults.backtest_lookback_days
        ),
        backtest_company_ids=_env_str(
            "BACKTEST_COMPANY_IDS", defaults.backtest_company_ids
        ),
    )
