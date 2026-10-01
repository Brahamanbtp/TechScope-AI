import html


def slack_payload(event: str, payload: dict) -> dict:
    return {"text": f"TechScope event: {event}\n{payload}"}


def discord_payload(event: str, payload: dict) -> dict:
    return {"content": f"**TechScope event: {event}**\n```json\n{payload}\n```"}


def telegram_payload(event: str, payload: dict) -> dict:
    return {"text": html.escape(f"TechScope event: {event}\n{payload}"), "parse_mode": "HTML"}


def matrix_payload(event: str, payload: dict) -> dict:
    body = f"TechScope event: {event}\n{payload}"
    return {"msgtype": "m.notice", "body": body, "format": "org.matrix.custom.html", "formatted_body": html.escape(body)}


def payload_for_adapter(adapter: str, event: str, payload: dict) -> dict:
    adapters = {"slack": slack_payload, "discord": discord_payload, "telegram": telegram_payload, "matrix": matrix_payload}
    if adapter not in adapters:
        raise ValueError(f"Unsupported notification adapter: {adapter}")
    return adapters[adapter](event, payload)
