import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import feedparser

from agentic_alert.models.schemas import Provider
from agentic_alert.sources import provider_registry
from agentic_alert.sources.provider_registry import fetch_news


def test_fetch_news_rss_file_uses_feedparser(monkeypatch) -> None:
    snapshot_path = (
        Path(__file__).resolve().parents[2] / "data/rss_snapshots/sample.xml"
    )
    provider = Provider(
        provider_id="p999",
        name="Test RSS",
        type="rss_file",
        base_url=f"file://{snapshot_path.as_posix()}",
        enabled=True,
    )

    published = datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc)
    published_parsed = published.utctimetuple()

    entry = feedparser.FeedParserDict(
        {
            "title": "Test title",
            "link": "https://example.com/item",
            "published_parsed": published_parsed,
            "summary": "Test summary",
        }
    )
    feed = feedparser.FeedParserDict({"entries": [entry]})

    def _mock_parse(_url, **_kwargs):
        return feed

    monkeypatch.setattr(feedparser, "parse", _mock_parse)

    results = fetch_news(provider, Path("data/articles.csv"))

    assert len(results) == 1
    item = results[0]
    assert item.title == "Test title"
    assert item.url == "https://example.com/item"
    assert item.source_name == "Test RSS"
    assert item.published_at == published.isoformat()


def test_fetch_news_rss_file_parses_snapshot() -> None:
    snapshot_path = (
        Path(__file__).resolve().parents[2] / "data/rss_snapshots/sample.xml"
    )
    provider = Provider(
        provider_id="p998",
        name="Snapshot RSS",
        type="rss_file",
        base_url=f"file://{snapshot_path.as_posix()}",
        enabled=True,
    )

    results = fetch_news(provider, Path("data/articles.csv"))

    assert len(results) > 0
    item = results[0]
    assert item.title
    assert item.url
    assert item.published_at
    assert item.content_snippet


def test_fetch_news_https_uses_certifi_bundle(monkeypatch) -> None:
    provider = Provider(
        provider_id="p997",
        name="Test HTTPS RSS",
        type="rss",
        base_url="https://example.com/rss",
        enabled=True,
    )

    captured = {}

    def _fake_where():
        return "/tmp/certifi.pem"

    def _fake_create_default_context(*, cafile=None):
        captured["cafile"] = cafile

        class DummyCtx:
            pass

        return DummyCtx()

    class DummyResp:
        status = 200
        headers = {"content-type": "application/rss+xml"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"<rss></rss>"

        def geturl(self):
            return "https://example.com/rss"

    def _fake_urlopen(request, context=None, timeout=None):
        captured["context"] = context
        captured["url"] = request.full_url
        captured["user_agent"] = request.get_header("User-agent") or request.get_header(
            "User-Agent"
        )
        return DummyResp()

    monkeypatch.setattr(certifi, "where", _fake_where)
    monkeypatch.setattr(ssl, "create_default_context", _fake_create_default_context)
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    def _fake_parse(data):
        captured["parse_arg"] = data
        return feedparser.FeedParserDict({"entries": []})

    monkeypatch.setattr(feedparser, "parse", _fake_parse)

    fetch_news(provider, Path("data/articles.csv"))

    assert captured["cafile"] == "/tmp/certifi.pem"
    assert captured["url"] == "https://example.com/rss"
    assert captured["context"].__class__.__name__ == "DummyCtx"
    assert captured["user_agent"] == "Mozilla/5.0 (AgenticAlert/0.1)"
    assert captured["parse_arg"] == b"<rss></rss>"


def test_fetch_news_gn_company_builds_query(monkeypatch) -> None:
    provider = Provider(
        provider_id="p996",
        name="Google News Company-Scoped (IT)",
        type="gn_company",
        base_url="https://news.google.com/rss/search",
        enabled=True,
    )

    rows = [
        {
            "company_id": "c001",
            "name": "Alpha Energia",
            "aliases": "Alpha Energia S.p.A.;Alpha Energia Italia",
            "website_domain": "alphaenergia.it",
            "country": "IT",
            "status": "active",
        }
    ]

    monkeypatch.setattr(provider_registry, "read_csv", lambda _path: rows)

    captured = {"urls": []}

    def _fake_parse(url):
        captured["urls"].append(url)
        return feedparser.FeedParserDict({"entries": []})

    monkeypatch.setattr(provider_registry, "_parse_rss_from_url", _fake_parse)
    monkeypatch.setattr(provider_registry.time, "sleep", lambda _s: None)

    fetch_news(provider, Path("data/articles.csv"))

    assert captured["urls"]
    url = captured["urls"][0]
    assert "news.google.com/rss/search?q=" in url
    assert "site%3Aalphaenergia.it" in url
    assert "-banca" in url


def test_fetch_news_rss_diagnostics_uses_requests(
    monkeypatch, capsys
) -> None:
    provider = Provider(
        provider_id="p123",
        name="Test RSS Diagnostics",
        type="rss",
        base_url="https://example.com/rss",
        enabled=True,
    )

    captured = {}

    class DummyResp:
        status_code = 200
        url = "https://example.com/rss"
        headers = {"content-type": "application/rss+xml"}
        content = b"<rss></rss>"

    def _fake_get(
        url,
        headers=None,
        timeout=None,
        allow_redirects=True,
        verify=None,
    ):
        captured["url"] = url
        captured["headers"] = headers or {}
        captured["timeout"] = timeout
        captured["allow_redirects"] = allow_redirects
        captured["verify"] = verify
        return DummyResp()

    monkeypatch.setattr(provider_registry.requests, "get", _fake_get)

    def _fake_parse(data):
        captured["parse_arg"] = data
        return feedparser.FeedParserDict({"entries": [], "bozo": 0})

    monkeypatch.setattr(feedparser, "parse", _fake_parse)
    monkeypatch.setenv("RSS_DIAGNOSTICS", "true")

    results = fetch_news(provider, Path("data/articles.csv"))

    assert results == []
    assert captured["url"] == "https://example.com/rss"
    assert captured["timeout"] == 15
    assert captured["allow_redirects"] is True
    assert captured["headers"].get("User-Agent") == "Mozilla/5.0 (AgenticAlert/0.1)"
    assert captured["parse_arg"] == b"<rss></rss>"
    assert captured["verify"] is None

    output = capsys.readouterr().out
    assert "p123 | https://example.com/rss | 200 | https://example.com/rss" in output


def test_gn_diagnostics_uses_certifi_verify(monkeypatch) -> None:
    provider = Provider(
        provider_id="gn_it_test",
        name="GN Test",
        type="rss",
        base_url="https://news.google.com/rss/search?q=test",
        enabled=True,
    )

    monkeypatch.setenv("RSS_DIAGNOSTICS", "true")

    monkeypatch.setattr(
        provider_registry.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("1.2.3.4", 443))],
    )

    class DummySock:
        def close(self):
            return None

    monkeypatch.setattr(
        provider_registry.socket,
        "create_connection",
        lambda *_args, **_kwargs: DummySock(),
    )

    class DummyTLS:
        def do_handshake(self):
            return None

        def close(self):
            return None

    class DummyCtx:
        def wrap_socket(self, sock, server_hostname=None):
            return DummyTLS()

    monkeypatch.setattr(
        provider_registry.ssl,
        "create_default_context",
        lambda *args, **kwargs: DummyCtx(),
    )

    monkeypatch.setattr(provider_registry.certifi, "where", lambda: "/tmp/ca.pem")

    captured = {}

    class DummyResp:
        status_code = 200
        url = "https://news.google.com/rss/search?q=test"
        headers = {"content-type": "application/rss+xml"}
        content = b"<rss></rss>"

    def _fake_get(
        url,
        headers=None,
        timeout=None,
        allow_redirects=True,
        verify=None,
    ):
        captured["verify"] = verify
        return DummyResp()

    monkeypatch.setattr(provider_registry.requests, "get", _fake_get)

    monkeypatch.setattr(
        feedparser,
        "parse",
        lambda data: feedparser.FeedParserDict({"entries": [], "bozo": 0}),
    )

    fetch_news(provider, Path("data/articles.csv"))

    assert captured["verify"] == "/tmp/ca.pem"
