import calendar
import hashlib
import json
import os
import random
import socket
import ssl
import time
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import certifi
import feedparser
import requests

from agentic_alert.models.schemas import Provider, NewsItem, Company, Trigger
from agentic_alert.storage.csv_store import read_csv


def fetch_news(
    provider: Provider,
    articles_path: Path,
    *,
    companies: list[Company] | None = None,
    triggers: list[Trigger] | None = None,
    lookback_days: int | None = None,
    backtest_mode: bool = False,
) -> list[NewsItem]:
    """Load RSS or dummy articles, depending on provider type."""
    if provider.type == "gdelt_doc":
        return _load_gdelt_doc(
            provider, companies, triggers, lookback_days, backtest_mode
        )

    if provider.type == "gdelt_snapshot":
        return _load_gdelt_snapshot(provider)

    if _is_rss_provider(provider):
        return _load_rss(provider, companies)

    if provider.type not in {"site_stub", "dummy"}:
        return []

    if not articles_path.exists():
        return []

    return _load_articles(articles_path, provider.provider_id)


def _is_rss_provider(provider: Provider) -> bool:
    return (
        provider.type in {"rss", "rss_file", "gn_company"}
        or provider.base_url.startswith("file://")
    )


def _is_gn_provider(provider: Provider) -> bool:
    return provider.name.startswith("GN_") or "news.google.com" in provider.base_url


def _load_rss(provider: Provider, companies: list[Company] | None) -> list[NewsItem]:
    if provider.type == "gn_company":
        return _load_gn_company(provider, companies)

    is_file = provider.type == "rss_file" or provider.base_url.startswith("file://")
    items: list[NewsItem] = []
    try:
        if is_file:
            feed_content = _read_rss_file(provider.base_url)
            feed = feedparser.parse(feed_content)
        else:
            diagnostics = _rss_diagnostics_enabled()
            if diagnostics and provider.type == "rss":
                feed = _fetch_rss_with_diagnostics(
                    provider, provider.base_url
                )
                if feed is None:
                    print(f"RSS {provider.name}: fetched 0 items")
                    return []
            else:
                if _is_gn_provider(provider):
                    print(f"GN SSL CA bundle: {_ca_bundle_path()}")
                feed = _parse_rss_from_url(provider.base_url)
            _log_gn_debug(provider, feed)
        items = _entries_to_items(provider, getattr(feed, "entries", []) or [])
    except Exception as exc:  # noqa: BLE001 - log and continue for failing providers
        if _is_gn_provider(provider):
            print(
                "GN debug "
                f"{provider.name}: exception={exc.__class__.__name__}: {exc}"
            )
        reason = str(exc).strip() or exc.__class__.__name__
        print(f"RSS {provider.name}: fetch failed: {reason}")
        return []

    log_suffix = " (file)" if is_file else ""
    print(f"RSS {provider.name}{log_suffix}: fetched {len(items)} items")
    return items


def _ca_bundle_path() -> str:
    return certifi.where()


def _fetch_url_bytes(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    ca = _ca_bundle_path()
    ctx = ssl.create_default_context(cafile=ca)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (AgenticAlert/0.1)"}
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001 - log and continue for failing providers
        if _is_ssl_verification_error(exc):
            print(
                "SSL verification failed. Ensure certifi is installed and used as CA bundle."
            )
        raise


def _parse_rss_from_url(url: str) -> feedparser.FeedParserDict:
    data = _fetch_url_bytes(url)
    return feedparser.parse(data)


def _companies_csv_path() -> Path:
    value = os.getenv("COMPANIES_CSV")
    return Path(value) if value else Path("data/companies.csv")

def _load_companies_from_csv(path: Path) -> list[Company]:
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


def _active_companies(companies: list[Company]) -> list[Company]:
    active: list[Company] = []
    for company in companies:
        status = company.status.strip().lower()
        if status and status != "active":
            continue
        if not company.name:
            continue
        active.append(company)
    return active


def _company_is_bank(company: Company) -> bool:
    value = getattr(company, "is_bank", "")
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    return normalized in {"1", "true", "yes", "y"}


def _gn_company_candidates(companies: list[Company]) -> list[Company]:
    candidates: list[Company] = []
    for company in _active_companies(companies):
        country = company.country.strip().upper()
        if country != "IT":
            continue
        if _company_is_bank(company):
            continue
        candidates.append(company)
    return candidates


def _gn_company_feeds_cap() -> int:
    value = os.getenv("GN_COMPANY_FEEDS_CAP")
    if not value:
        return 50
    try:
        cap = int(value)
    except ValueError:
        return 50
    return max(cap, 0)


def _gn_company_feeds_mode() -> str:
    value = os.getenv("GN_COMPANY_FEEDS_MODE", "top_revenue").strip().lower()
    if value in {"top_revenue", "random", "rolling"}:
        return value
    return "top_revenue"


def _gn_company_feeds_seed() -> str:
    return os.getenv("GN_COMPANY_FEEDS_SEED", "").strip()


def _parse_revenue_value(value: str) -> float:
    if not value:
        return 0.0
    cleaned = value.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _seed_to_int(seed: str) -> int:
    if not seed:
        return 0
    value = seed.strip()
    if not value:
        return 0
    if len(value) >= 10:
        try:
            parsed = datetime.fromisoformat(value[:10])
            return parsed.date().toordinal()
        except ValueError:
            pass
    try:
        return int(value)
    except ValueError:
        pass
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _rolling_window(
    items: list[Company],
    cap: int,
    start: int,
) -> list[Company]:
    if cap >= len(items):
        return items
    end = start + cap
    if end <= len(items):
        return items[start:end]
    return items[start:] + items[: end - len(items)]


def _select_top_revenue(
    companies: list[Company],
    cap: int,
) -> list[Company]:
    ordered = sorted(companies, key=lambda company: company.company_id or "")
    ordered = sorted(
        ordered,
        key=lambda company: _parse_revenue_value(company.revenue_eur),
        reverse=True,
    )
    return ordered[:cap]


def _select_random(
    companies: list[Company],
    cap: int,
    seed: str,
) -> list[Company]:
    ordered = sorted(companies, key=lambda company: company.company_id or "")
    rng = random.Random(_seed_to_int(seed))
    rng.shuffle(ordered)
    return ordered[:cap]


def _select_rolling(
    companies: list[Company],
    cap: int,
    seed: str,
) -> list[Company]:
    ordered = sorted(companies, key=lambda company: company.company_id or "")
    if not ordered:
        return []
    if cap >= len(ordered):
        return ordered
    start = _seed_to_int(seed) % len(ordered)
    return _rolling_window(ordered, cap, start)


def _select_gn_companies(
    companies: list[Company],
    cap: int,
    mode: str,
    seed: str,
) -> list[Company]:
    if cap <= 0 or not companies:
        return []
    if mode == "random":
        return _select_random(companies, cap, seed)
    if mode == "rolling":
        return _select_rolling(companies, cap, seed)
    return _select_top_revenue(companies, cap)


def _load_gn_company(
    provider: Provider,
    companies: list[Company] | None,
) -> list[NewsItem]:
    if companies is None:
        companies = _load_companies_from_csv(_companies_csv_path())
    candidates = _gn_company_candidates(companies)
    cap = _gn_company_feeds_cap()
    mode = _gn_company_feeds_mode()
    seed = _gn_company_feeds_seed()
    companies = _select_gn_companies(candidates, cap, mode, seed)
    seed_label = seed if seed else "n/a"
    skipped = max(len(candidates) - len(companies), 0)
    if _is_gn_provider(provider) and not _rss_diagnostics_enabled():
        print(f"GN SSL CA bundle: {_ca_bundle_path()}")
    if _rss_diagnostics_enabled():
        sample_url = provider.base_url
        for company in companies:
            query = _build_gn_company_query(company)
            if query:
                sample_url = _build_gn_company_url(provider.base_url, query)
                break
        _fetch_rss_with_diagnostics(provider, sample_url)
    print(
        "GN company feeds processed: "
        f"{len(companies)} (cap={cap} mode={mode} seed={seed_label})"
    )
    print(f"GN company feeds skipped: {skipped}")

    items: list[NewsItem] = []
    for idx, company in enumerate(companies):
        company_id = company.company_id or "unknown"
        query = _build_gn_company_query(company)
        if not query:
            continue
        url = _build_gn_company_url(provider.base_url, query)
        try:
            feed = _parse_rss_from_url(url)
        except Exception as exc:  # noqa: BLE001 - log and continue
            reason = str(exc).strip() or exc.__class__.__name__
            print(f"GN company feed failed for {company_id}: {reason}")
            continue
        entries = getattr(feed, "entries", []) or []
        items.extend(
            _entries_to_items_for_company(provider, company_id, entries)
        )
        if idx < len(companies) - 1:
            time.sleep(1)
    return items


def _build_gn_company_query(company: Company) -> str:
    name = company.name.strip()
    if not name:
        return ""
    aliases = [alias.strip() for alias in company.aliases if alias.strip()]
    website_domain = company.website_domain.strip()
    terms = [name] + aliases
    seen: set[str] = set()
    parts: list[str] = []
    for term in terms:
        cleaned = term.replace("\"", "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(f"\"{cleaned}\"")
    if website_domain:
        parts.append(f"site:{website_domain}")
    if not parts:
        return ""
    query = "(" + " OR ".join(parts) + ") -banca -banche -bank -banks"
    return query


def _collect_trigger_keywords(triggers: list[Trigger] | None) -> list[str]:
    keywords: list[str] = []
    seen: set[str] = set()
    for trigger in triggers or []:
        for keyword in trigger.keywords:
            cleaned = keyword.replace("\"", "").strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            keywords.append(cleaned)
    return keywords


def _build_gdelt_query(company: Company, trigger_keywords: list[str]) -> str:
    terms = [company.name] + list(company.aliases)
    parts: list[str] = []
    seen: set[str] = set()
    for term in terms:
        cleaned = term.replace("\"", "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(f"\"{cleaned}\"")
    if company.website_domain:
        parts.append(f"site:{company.website_domain}")
    if not parts:
        return ""
    company_clause = "(" + " OR ".join(parts) + ")"
    if not trigger_keywords:
        return company_clause
    keyword_clause = "(" + " OR ".join(f"\"{kw}\"" for kw in trigger_keywords) + ")"
    return f"{company_clause} AND {keyword_clause}"


def _parse_gdelt_seendate(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    for fmt in ("%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def _load_gdelt_doc(
    provider: Provider,
    companies: list[Company] | None,
    triggers: list[Trigger] | None,
    lookback_days: int | None,
    backtest_mode: bool,
) -> list[NewsItem]:
    """Fetch GDELT Doc 2.0 articles with a capped, rolling lookback window."""
    if companies is None:
        companies = _load_companies_from_csv(_companies_csv_path())
    companies = _active_companies(companies)
    trigger_keywords = _collect_trigger_keywords(triggers)
    window_days = lookback_days if lookback_days and lookback_days > 0 else 14
    max_records = 250
    items: list[NewsItem] = []
    had_failure = False

    endpoint = "https://api.gdeltproject.org/api/v2/doc/doc"

    for company in companies:
        query = _build_gdelt_query(company, trigger_keywords)
        if not query:
            continue
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "timespan": f"{window_days}d",
            "maxrecords": str(max_records),
        }
        try:
            response = requests.get(endpoint, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001 - log and continue
            reason = str(exc).strip() or exc.__class__.__name__
            print(f"GDELT {provider.name}: fetch failed for {company.company_id}: {reason}")
            had_failure = True
            continue

        articles = payload.get("articles") or payload.get("results") or []
        for article in articles[:max_records]:
            url = article.get("url") or ""
            if not url:
                continue
            title = article.get("title") or "TBD"
            published_at = _parse_gdelt_seendate(
                article.get("seendate") or article.get("date") or ""
            )
            article_id = hashlib.sha256(
                f"{provider.provider_id}:{url}".encode("utf-8")
            ).hexdigest()
            content_snippet = (
                article.get("sourcecountry")
                or article.get("domain")
                or article.get("language")
                or ""
            )
            items.append(
                NewsItem(
                    article_id=article_id,
                    provider_id=provider.provider_id,
                    source_name="GDELT",
                    title=title,
                    url=url,
                    published_at=published_at,
                    content_snippet=content_snippet,
                )
            )
    print(f"GDELT {provider.name}: fetched {len(items)} items")
    if backtest_mode and had_failure and not items:
        print(
            "GDELT live fetch failed (network). "
            "Use gdelt_snapshot for offline validation."
        )
    return items


def _load_gdelt_snapshot(provider: Provider) -> list[NewsItem]:
    try:
        entries = _read_gdelt_snapshot(provider.base_url)
    except Exception as exc:  # noqa: BLE001 - log and continue
        reason = str(exc).strip() or exc.__class__.__name__
        print(f"GDELT {provider.name}: fetch failed: {reason}")
        return []

    items: list[NewsItem] = []
    for index, entry in enumerate(entries):
        title = entry.get("title") or "TBD"
        url = entry.get("url") or ""
        published_at = _normalize_timestamp(entry.get("published_at") or "")
        source = entry.get("source") or provider.name
        snippet = entry.get("snippet") or ""
        if not url:
            url = f"{provider.provider_id}-snapshot-{index + 1}"
        article_id = hashlib.sha256(
            f"{provider.provider_id}:{url}".encode("utf-8")
        ).hexdigest()
        items.append(
            NewsItem(
                article_id=article_id,
                provider_id=provider.provider_id,
                source_name=source,
                title=title,
                url=url,
                published_at=published_at,
                content_snippet=snippet,
            )
        )
    print(f"GDELT {provider.name}: fetched {len(items)} items")
    return items


def _read_gdelt_snapshot(base_url: str) -> list[dict]:
    if not base_url:
        raise ValueError("Missing base_url for gdelt_snapshot")
    path = (
        Path(base_url.replace("file://", "", 1))
        if base_url.startswith("file://")
        else Path(base_url)
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Snapshot JSON must be a list of items")
    return payload


def _normalize_timestamp(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    if value.endswith("Z"):
        return value[:-1] + "+00:00"
    return value


def _build_gn_company_url(base_url: str, query: str) -> str:
    base = base_url if base_url else "https://news.google.com/rss/search"
    encoded = urllib.parse.quote(query)
    return f"{base}?q={encoded}&hl=it&gl=IT&ceid=IT:it"


def _entries_to_items_for_company(
    provider: Provider,
    company_id: str,
    entries: list[feedparser.FeedParserDict],
) -> list[NewsItem]:
    items: list[NewsItem] = []
    for index, entry in enumerate(entries):
        published_at = _published_at(entry)
        article_id = (
            entry.get("id")
            or entry.get("guid")
            or entry.get("link")
            or f"{provider.provider_id}-{company_id}-{index + 1}"
        )
        items.append(
            NewsItem(
                article_id=str(article_id),
                provider_id=provider.provider_id,
                source_name=f"GN Company | {company_id}",
                title=entry.get("title", "TBD"),
                url=entry.get("link", "TBD"),
                published_at=published_at,
                content_snippet=entry.get("summary")
                or entry.get("description")
                or "TBD",
            )
        )
    return items


def _is_ssl_verification_error(exc: Exception) -> bool:
    if isinstance(exc, ssl.SSLError):
        return True
    if isinstance(exc, urllib.error.URLError) and isinstance(
        exc.reason, ssl.SSLError
    ):
        return True
    return "CERTIFICATE_VERIFY_FAILED" in str(exc)


def _log_gn_debug(provider: Provider, feed: feedparser.FeedParserDict) -> None:
    if _rss_diagnostics_enabled():
        return
    if not _is_gn_provider(provider):
        return
    bozo = getattr(feed, "bozo", None)
    bozo_exc = getattr(feed, "bozo_exception", None)
    status = getattr(feed, "status", None)
    href = getattr(feed, "href", None)
    entries = getattr(feed, "entries", None) or []
    headers = {}
    try:
        headers = feed.get("headers", {}) or {}
    except Exception:
        headers = {}
    content_type = None
    location = None
    if isinstance(headers, dict):
        content_type = headers.get("content-type") or headers.get("Content-Type")
        location = headers.get("location") or headers.get("Location")
    bozo_exc_text = str(bozo_exc) if bozo_exc is not None else None
    print(
        "GN debug "
        f"{provider.name}: status={status} bozo={bozo} "
        f"bozo_exception={bozo_exc_text} href={href} "
        f"entries={len(entries)} content-type={content_type} "
        f"location={location}"
    )


def _entries_to_items(
    provider: Provider,
    entries: list[feedparser.FeedParserDict],
) -> list[NewsItem]:
    items: list[NewsItem] = []
    for index, entry in enumerate(entries):
        published_at = _published_at(entry)
        article_id = (
            entry.get("id")
            or entry.get("guid")
            or entry.get("link")
            or f"{provider.provider_id}-{index + 1}"
        )
        items.append(
            NewsItem(
                article_id=str(article_id),
                provider_id=provider.provider_id,
                source_name=provider.name,
                title=entry.get("title", "TBD"),
                url=entry.get("link", "TBD"),
                published_at=published_at,
                content_snippet=entry.get("summary")
                or entry.get("description")
                or "TBD",
            )
        )
    return items


def _published_at(entry: feedparser.FeedParserDict) -> str:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        timestamp = calendar.timegm(published)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def _read_rss_file(base_url: str) -> bytes:
    path = Path(base_url.replace("file://", "", 1))
    return path.read_bytes()


def _load_articles(path: Path, provider_id: str) -> list[NewsItem]:
    rows = read_csv(path)
    items: list[NewsItem] = []
    for row in rows:
        if row.get("provider_id") != provider_id:
            continue
        items.append(
            NewsItem(
                article_id=row.get("article_id", ""),
                provider_id=row.get("provider_id", ""),
                source_name=row.get("source_name", ""),
                title=row.get("title", ""),
                url=row.get("url", ""),
                published_at=row.get("published_at", ""),
                content_snippet=row.get("content_snippet", ""),
            )
        )
    return items


def _rss_diagnostics_enabled() -> bool:
    value = os.getenv("RSS_DIAGNOSTICS")
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def _is_gn_provider_id(provider_id: str) -> bool:
    normalized = provider_id.strip().lower()
    return normalized.startswith("gn_") or normalized.startswith("gn_company_")


def _short_text(value: str, max_len: int = 140) -> str:
    cleaned = value.replace("\n", " ").strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3] + "..."


def _gn_preflight(host: str = "news.google.com") -> dict[str, str]:
    dns_status = "fail"
    ip_count = "0"
    first_ip = ""
    dns_err = ""
    try:
        infos = socket.getaddrinfo(host, 443)
        ips = sorted({info[4][0] for info in infos if info and info[4]})
        dns_status = "ok"
        ip_count = str(len(ips))
        if ips:
            first_ip = ips[0]
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        dns_err = _short_text(str(exc))

    tcp_status = "fail"
    tcp_err = ""
    tls_status = "fail"
    tls_err = ""
    sock = None
    tls_sock = None
    try:
        sock = socket.create_connection((host, 443), timeout=5)
        tcp_status = "ok"
        ctx = ssl.create_default_context(cafile=certifi.where())
        tls_sock = ctx.wrap_socket(sock, server_hostname=host)
        tls_sock.do_handshake()
        tls_status = "ok"
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        if tcp_status != "ok":
            tcp_err = _short_text(str(exc))
        else:
            tls_err = f"{exc.__class__.__name__}: {_short_text(str(exc))}"
    finally:
        try:
            if tls_sock:
                tls_sock.close()
        except Exception:
            pass
        try:
            if sock:
                sock.close()
        except Exception:
            pass

    result = {
        "dns": dns_status,
        "ips": ip_count,
        "ip": first_ip,
        "dns_err": dns_err,
        "tcp": tcp_status,
        "tcp_err": tcp_err,
        "tls": tls_status,
        "tls_err": tls_err,
    }
    return result


def _format_gn_preflight(
    provider_id: str, preflight: dict[str, str], req_status: str
) -> str:
    parts = [
        f"GN_PREFLIGHT {provider_id}",
        f"dns={preflight.get('dns')}",
        f"ips={preflight.get('ips')}",
    ]
    if preflight.get("ip"):
        parts.append(f"ip={preflight.get('ip')}")
    if preflight.get("dns") != "ok" and preflight.get("dns_err"):
        parts.append(f"dns_err={preflight.get('dns_err')}")
    parts.append(f"tcp={preflight.get('tcp')}")
    if preflight.get("tcp") != "ok" and preflight.get("tcp_err"):
        parts.append(f"tcp_err={preflight.get('tcp_err')}")
    parts.append(f"tls={preflight.get('tls')}")
    if preflight.get("tls") != "ok" and preflight.get("tls_err"):
        parts.append(f"tls_err={preflight.get('tls_err')}")
    parts.append(f"req={req_status}")
    return " ".join(parts)


def _fetch_rss_with_diagnostics(
    provider: Provider, url: str
) -> feedparser.FeedParserDict | None:
    headers = {"User-Agent": "Mozilla/5.0 (AgenticAlert/0.1)"}
    preflight = None
    if _is_gn_provider_id(provider.provider_id):
        preflight = _gn_preflight()
    req_status = "ERR"
    try:
        request_kwargs = {
            "headers": headers,
            "timeout": 15,
            "allow_redirects": True,
        }
        if _is_gn_provider_id(provider.provider_id):
            request_kwargs["verify"] = certifi.where()
        response = requests.get(url, **request_kwargs)
        status = response.status_code
        req_status = str(status)
        final_url = response.url or ""
        content_type = response.headers.get("content-type") or response.headers.get(
            "Content-Type"
        )
        data = response.content or b""
        feed = feedparser.parse(data)
        bozo = getattr(feed, "bozo", None)
        bozo_exc = getattr(feed, "bozo_exception", None)
        bozo_text = _short_text(str(bozo_exc)) if bozo_exc else ""
        entries_count = len(getattr(feed, "entries", []) or [])
        if preflight:
            print(_format_gn_preflight(provider.provider_id, preflight, req_status))
        print(
            f"{provider.provider_id} | {url} | {status} | {final_url} | "
            f"{content_type or ''} | {len(data)} | {bozo} | {bozo_text} | "
            f"{entries_count}"
        )
        return feed
    except Exception as exc:  # noqa: BLE001 - log and continue
        bozo_text = _short_text(str(exc))
        if preflight:
            print(_format_gn_preflight(provider.provider_id, preflight, req_status))
        print(
            f"{provider.provider_id} | {url} | ERR |  |  | 0 |  | {bozo_text} | 0"
        )
        return None
