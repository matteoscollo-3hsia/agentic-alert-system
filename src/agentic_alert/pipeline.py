import os
import re
import uuid
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path

from agentic_alert.alerts.dispatcher import dispatch_alerts
from agentic_alert.config import AppConfig, load_config
from agentic_alert.models.schemas import (
    Alert,
    AlertCandidate,
    Company,
    NewsItem,
    Provider,
    Trigger,
)
from agentic_alert.sources.provider_registry import fetch_news
from agentic_alert.storage.csv_store import read_csv, write_csv
from agentic_alert.triggers.matcher import match_triggers


@dataclass
class CompanyMatch:
    company: Company
    match_method: str
    confidence: float


def load_companies(path: Path) -> list[Company]:
    rows = read_csv(path)
    companies: list[Company] = []
    for row in rows:
        aliases_raw = row.get("aliases", "")
        aliases = [alias.strip() for alias in aliases_raw.split(";") if alias.strip()]
        companies.append(
            Company(
                company_id=row.get("company_id", ""),
                name=row.get("name", ""),
                aliases=aliases,
                revenue_eur=row.get("revenue_eur", ""),
                industry_code=row.get("industry_code", ""),
                industry_description=row.get("industry_description", ""),
                website=row.get("website", ""),
                website_domain=row.get("website_domain", ""),
                country=row.get("country", ""),
                contact_owner=row.get("contact_owner", ""),
                status=row.get("status", ""),
            )
        )
    return companies


def load_triggers(path: Path) -> list[Trigger]:
    rows = read_csv(path)
    triggers: list[Trigger] = []
    for row in rows:
        keywords_raw = row.get("keywords", "")
        keywords = [keyword.strip() for keyword in keywords_raw.split(";") if keyword.strip()]
        triggers.append(
            Trigger(
                trigger_id=row.get("trigger_id", ""),
                name=row.get("name", ""),
                keywords=keywords,
                priority=row.get("priority", ""),
                description=row.get("description", ""),
            )
        )
    return triggers


def load_providers(path: Path) -> list[Provider]:
    rows = read_csv(path)
    providers: list[Provider] = []
    for row in rows:
        providers.append(
            Provider(
                provider_id=row.get("provider_id", ""),
                name=row.get("name", ""),
                type=row.get("type", ""),
                base_url=row.get("base_url", ""),
                enabled=_parse_bool(row.get("enabled", ""), True),
            )
        )
    return providers


def _parse_bool(value: str, default: bool) -> bool:
    if not value:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    return default


def _filter_companies_by_ids(
    companies: list[Company],
    company_ids_csv: str,
) -> list[Company]:
    if not company_ids_csv:
        return companies
    target_ids = {
        company_id.strip().lower()
        for company_id in company_ids_csv.split(",")
        if company_id.strip()
    }
    if not target_ids:
        return companies
    return [
        company
        for company in companies
        if company.company_id.lower() in target_ids
    ]


def _article_text(news_item: NewsItem) -> str:
    return f"{news_item.title} {news_item.content_snippet}".strip()


def match_companies(news_item: NewsItem, companies: list[Company]) -> list[CompanyMatch]:
    text = _article_text(news_item).lower()
    snippet = news_item.content_snippet.lower()
    url = news_item.url.lower()
    matches: dict[str, CompanyMatch] = {}

    for company in companies:
        if company.status and company.status.lower() != "active":
            continue
        if company.website_domain:
            domain = company.website_domain.lower()
            if domain in url or domain in snippet:
                _update_match(matches, company, "domain", 0.95)
        for alias in company.aliases:
            if alias.lower() in text:
                _update_match(matches, company, "alias", 0.85)
        if company.name and company.name.lower() in text:
            _update_match(matches, company, "name", 0.75)

    return list(matches.values())


def _update_match(
    matches: dict[str, CompanyMatch],
    company: Company,
    method: str,
    confidence: float,
) -> None:
    current = matches.get(company.company_id)
    if current and current.confidence >= confidence:
        return

    matches[company.company_id] = CompanyMatch(
        company=company,
        match_method=method,
        confidence=confidence,
    )


def _resolve_contact_owner(company: Company) -> str:
    return company.contact_owner if company.contact_owner else "N/A"


_DATE_PREFIX_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}$")


def _normalize_title(title: str) -> str:
    if not title:
        return ""
    lowered = title.strip().lower()
    cleaned = "".join(
        ch if ch.isalnum() or ch.isspace() else " " for ch in lowered
    )
    return " ".join(cleaned.split())


def _published_date(published_at: str) -> str:
    if not published_at:
        return "unknown"
    value = published_at.strip()
    if not value:
        return "unknown"

    cleaned = value
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        candidate = value[:10]
        if len(candidate) == 10 and _DATE_PREFIX_RE.match(candidate):
            return candidate
        return "unknown"

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.date().isoformat()


def _build_dedupe_key(
    company_id: str,
    trigger_id: str,
    published_at: str,
    title: str,
) -> str:
    published_date = _published_date(published_at)
    norm_title = _normalize_title(title)
    return f"{company_id}|{trigger_id}|{published_date}|{norm_title}"


def _is_env_override(name: str) -> bool:
    return bool(os.getenv(name))


def _resolved_path(path: Path) -> str:
    return str(path.resolve())


def _company_is_active(company: Company) -> bool:
    status = company.status.strip().lower()
    return not status or status == "active"


def _print_provenance(
    config: AppConfig,
    companies: list[Company],
    triggers: list[Trigger],
    providers: list[Provider],
    *,
    is_backtest: bool,
) -> None:
    companies_active = sum(1 for company in companies if _company_is_active(company))
    first_company_id = companies[0].company_id if companies else "n/a"
    last_company_id = companies[-1].company_id if companies else "n/a"
    enabled_providers = [provider for provider in providers if provider.enabled]
    first_enabled_provider_id = (
        enabled_providers[0].provider_id if enabled_providers else "n/a"
    )
    first_trigger_id = triggers[0].trigger_id if triggers else "n/a"

    print("PROVENANCE")
    print(
        f"Using companies_csv: {_resolved_path(config.companies_csv)} "
        f"(override: {_is_env_override('COMPANIES_CSV')})"
    )
    print(
        f"Using triggers_csv: {_resolved_path(config.triggers_csv)} "
        f"(override: {_is_env_override('TRIGGERS_CSV')})"
    )
    print(
        f"Using providers_csv: {_resolved_path(config.providers_csv)} "
        f"(override: {_is_env_override('PROVIDERS_CSV')})"
    )
    print(
        f"Using alerts_csv: {_resolved_path(config.alerts_csv)} "
        f"(override: {_is_env_override('ALERTS_CSV')})"
    )
    if is_backtest:
        print(
            "Using backtest_output_csv: "
            f"{_resolved_path(config.backtest_output_csv)} "
            f"(override: {_is_env_override('BACKTEST_OUTPUT_CSV')})"
        )

    print(
        "companies: "
        f"rows_loaded={len(companies)} "
        f"rows_active={companies_active} "
        f"first_company_id={first_company_id} "
        f"last_company_id={last_company_id}"
    )
    print(
        "triggers: "
        f"count={len(triggers)} "
        f"first_trigger_id={first_trigger_id}"
    )
    print(
        "providers: "
        f"rows_loaded={len(providers)} "
        f"enabled_count={len(enabled_providers)} "
        f"first_enabled_provider_id={first_enabled_provider_id}"
    )


def load_existing_alert_keys(path: Path) -> set[str]:
    rows = read_csv(path)
    keys: set[str] = set()
    for row in rows:
        company_id = row.get("company_id", "")
        trigger_id = row.get("trigger_id", "")
        if not company_id or not trigger_id:
            continue

        dedupe_key = row.get("dedupe_key", "")
        if not dedupe_key:
            title = row.get("title") or row.get("article_title") or ""
            dedupe_key = _build_dedupe_key(
                company_id,
                trigger_id,
                row.get("published_at", ""),
                title,
            )
        if dedupe_key:
            keys.add(dedupe_key)
    return keys


def _alert_fieldnames() -> list[str]:
    return [field.name for field in fields(Alert)]


def _ensure_backtest_header(path: Path) -> None:
    if path.exists():
        return
    fieldnames = _alert_fieldnames() + ["run_type"]
    write_csv(path, [], fieldnames, append=False)


def update_alert_statuses(
    path: Path,
    alert_ids: set[str],
    status: str,
) -> None:
    if not alert_ids:
        return

    rows = read_csv(path)
    if not rows:
        return

    for row in rows:
        if row.get("alert_id") in alert_ids:
            row["status"] = status

    fieldnames = list(rows[0].keys())
    write_csv(path, rows, fieldnames, append=False)


def build_alerts_for_article(
    news_item: NewsItem,
    company_matches: list[CompanyMatch],
    triggers: list[Trigger],
    created_at: str,
) -> tuple[list[AlertCandidate], list[Alert]]:
    candidates: list[AlertCandidate] = []
    alerts: list[Alert] = []
    normalized_title = _normalize_title(news_item.title)
    published_date = _published_date(news_item.published_at)

    for company_match in company_matches:
        for trigger in triggers:
            candidate_id = str(uuid.uuid4())
            candidates.append(
                AlertCandidate(
                    candidate_id=candidate_id,
                    article_id=news_item.article_id,
                    company_id=company_match.company.company_id,
                    trigger_id=trigger.trigger_id,
                    match_method=company_match.match_method,
                    confidence=company_match.confidence,
                )
            )

            contact_owner = _resolve_contact_owner(company_match.company)
            alerts.append(
                Alert(
                    alert_id=str(uuid.uuid4()),
                    company_id=company_match.company.company_id,
                    company_name=company_match.company.name,
                    trigger_id=trigger.trigger_id,
                    trigger_name=trigger.name,
                    contact_owner=contact_owner,
                    source=news_item.source_name,
                    article_url=news_item.url,
                    published_at=news_item.published_at,
                    dedupe_key=(
                        f"{company_match.company.company_id}|"
                        f"{trigger.trigger_id}|"
                        f"{published_date}|"
                        f"{normalized_title}"
                    ),
                    created_at=created_at,
                    status="new",
                )
            )

    return candidates, alerts


def _select_providers(
    providers: list[Provider],
    backtest_enabled: bool,
) -> list[Provider]:
    if not backtest_enabled:
        return [provider for provider in providers if provider.enabled]
    return [
        provider
        for provider in providers
        if provider.enabled or provider.type == "gdelt_doc"
    ]


def run_daily() -> None:
    config = load_config()
    _run_pipeline(config)


def _run_pipeline(config: AppConfig) -> None:
    is_backtest = config.backtest_enabled
    if (
        config.alerts_enabled
        and config.alert_channel == "slack"
        and not config.slack_webhook_url
    ):
        print(
            "ERROR: ALERTS_ENABLED=true and ALERT_CHANNEL=slack, but "
            "SLACK_WEBHOOK_URL is empty."
        )
        raise SystemExit(1)
    companies = load_companies(config.companies_csv)
    if is_backtest:
        companies = _filter_companies_by_ids(
            companies, config.backtest_company_ids
        )
    triggers = load_triggers(config.triggers_csv)
    all_providers = load_providers(config.providers_csv)
    _print_provenance(
        config,
        companies,
        triggers,
        all_providers,
        is_backtest=is_backtest,
    )
    providers = _select_providers(all_providers, is_backtest)
    print(f"Providers processed: {len(providers)}")

    all_candidates: list[AlertCandidate] = []
    all_alerts: list[Alert] = []
    created_at = datetime.now(timezone.utc).isoformat()
    total_news_items = 0

    for provider in providers:
        news_items = fetch_news(
            provider,
            config.articles_csv,
            companies=companies,
            triggers=triggers,
            lookback_days=config.backtest_lookback_days if is_backtest else None,
            backtest_mode=is_backtest,
        )
        total_news_items += len(news_items)
        for news_item in news_items:
            company_matches = match_companies(news_item, companies)
            if not company_matches:
                continue
            matched_triggers = match_triggers(_article_text(news_item), triggers)
            if not matched_triggers:
                continue

            candidates, alerts = build_alerts_for_article(
                news_item,
                company_matches,
                matched_triggers,
                created_at,
            )
            all_candidates.extend(candidates)
            all_alerts.extend(alerts)

    if all_candidates:
        rows = [asdict(candidate) for candidate in all_candidates]
        fieldnames = list(rows[0].keys())
        write_csv(config.alert_candidates_csv, rows, fieldnames, append=True)

    output_alerts_path = (
        config.backtest_output_csv if is_backtest else config.alerts_csv
    )
    existing_alert_keys = load_existing_alert_keys(output_alerts_path)
    new_alerts: list[Alert] = []
    for alert in all_alerts:
        key = alert.dedupe_key
        if key in existing_alert_keys:
            continue
        existing_alert_keys.add(key)
        new_alerts.append(alert)

    dedupe_skipped = len(all_alerts) - len(new_alerts)
    print(
        "Total news items: "
        f"{total_news_items} | Alerts generated: {len(new_alerts)} | "
        f"Dedupe skipped: {dedupe_skipped}"
    )

    if new_alerts:
        rows = [asdict(alert) for alert in new_alerts]
        if is_backtest:
            for row in rows:
                row["run_type"] = "backtest"
        fieldnames = list(rows[0].keys())
        write_csv(output_alerts_path, rows, fieldnames, append=True)
    elif is_backtest:
        _ensure_backtest_header(output_alerts_path)

    sent_ids = dispatch_alerts(
        new_alerts,
        config.alert_channel,
        config.alerts_enabled,
        config.slack_webhook_url,
    )
    if sent_ids:
        update_alert_statuses(output_alerts_path, sent_ids, "sent")


if __name__ == "__main__":
    run_daily()
