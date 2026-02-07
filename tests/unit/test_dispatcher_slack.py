from agentic_alert.alerts import dispatcher
from agentic_alert.models.schemas import Alert


def _make_alert(alert_id: str) -> Alert:
    return Alert(
        alert_id=alert_id,
        company_id="c001",
        company_name="Futura Tech S.p.A.",
        trigger_id="t001",
        trigger_name="Acquisizione",
        contact_owner="laura.bianchi@teha.it",
        source="Local RSS Snapshot",
        article_url="https://local.example.com/futura-tech-plan",
        published_at="2026-02-06T08:30:00Z",
        dedupe_key="c001|t001|2026-02-06|futura tech s p a",
        created_at="2026-02-06T12:00:00Z",
        status="new",
    )


def test_dispatch_slack_sends_when_enabled(monkeypatch) -> None:
    alerts = [_make_alert("al001"), _make_alert("al002")]
    calls: list[tuple[str, dict, int]] = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))

        class Response:
            status_code = 200

        return Response()

    monkeypatch.setattr(dispatcher.requests, "post", fake_post)

    sent_ids = dispatcher.dispatch_alerts(
        alerts,
        channel="slack",
        enabled=True,
        slack_webhook_url="https://hooks.slack.com/services/T000/B000/XXX",
    )

    assert len(calls) == 2
    assert sent_ids == {"al001", "al002"}


def test_dispatch_slack_skips_when_disabled(monkeypatch) -> None:
    alerts = [_make_alert("al003")]
    calls: list[tuple[str, dict, int]] = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))

        class Response:
            status_code = 200

        return Response()

    monkeypatch.setattr(dispatcher.requests, "post", fake_post)

    sent_ids = dispatcher.dispatch_alerts(
        alerts,
        channel="slack",
        enabled=False,
        slack_webhook_url="https://hooks.slack.com/services/T000/B000/XXX",
    )

    assert calls == []
    assert sent_ids == set()
