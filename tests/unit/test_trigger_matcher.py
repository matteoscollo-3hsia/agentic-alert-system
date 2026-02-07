from agentic_alert.models.schemas import Trigger
from agentic_alert.triggers.matcher import match_triggers


def test_match_triggers_returns_expected_matches() -> None:
    triggers = [
        Trigger(
            trigger_id="t001",
            name="Acquisizione",
            keywords=["acquisizione", "M&A"],
            priority="high",
            description="M&A events",
        ),
        Trigger(
            trigger_id="t002",
            name="Cambio CEO",
            keywords=["nuovo CEO", "CEO change"],
            priority="medium",
            description="Leadership change",
        ),
    ]

    text = "NordWind completa acquisizione di SolarPeak con nuovo CEO in carica."
    matched = match_triggers(text, triggers)
    matched_ids = {trigger.trigger_id for trigger in matched}

    assert matched_ids == {"t001", "t002"}
