from agentic_alert.models.schemas import Trigger


def match_triggers(text: str, triggers: list[Trigger]) -> list[Trigger]:
    haystack = text.lower()
    matched: list[Trigger] = []
    for trigger in triggers:
        for keyword in trigger.keywords:
            if keyword.lower() in haystack:
                matched.append(trigger)
                break
    return matched
