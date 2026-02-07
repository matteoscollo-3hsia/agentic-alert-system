from __future__ import annotations

import requests

from agentic_alert.models.schemas import Alert


def dispatch_alerts(
    alerts: list[Alert],
    channel: str,
    enabled: bool,
    slack_webhook_url: str,
) -> set[str]:
    """Print alerts to console and optionally dispatch to Slack."""
    if not alerts:
        print("No alerts generated.")
        return set()

    print(f"Alerts generated: {len(alerts)}")
    for alert in alerts:
        print(
            "ALERT | "
            f"{alert.company_name} | "
            f"{alert.trigger_name} | "
            f"{alert.contact_owner} | "
            f"{alert.source} | "
            f"{alert.article_url}"
        )

    if not enabled:
        print("Dispatch disabled. Set ALERTS_ENABLED=true to enable.")
        return set()

    if channel != "slack":
        return set()

    if not slack_webhook_url:
        print("Slack webhook URL not set. Skipping dispatch.")
        return set()

    sent_ids: set[str] = set()
    for alert in alerts:
        payload = {
            "text": (
                f"[{alert.trigger_name}] {alert.company_name} | "
                f"{alert.contact_owner} | {alert.source} | {alert.article_url}"
            )
        }
        try:
            response = requests.post(
                slack_webhook_url,
                json=payload,
                timeout=5,
            )
        except requests.RequestException as exc:
            print(f"Slack send failed: {exc}")
            continue

        if not 200 <= response.status_code < 300:
            print(f"Slack send failed: status {response.status_code}")
            continue

        sent_ids.add(alert.alert_id)

    return sent_ids
