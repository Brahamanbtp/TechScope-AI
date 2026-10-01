import logging
import time

import httpx

from storage.webhook_repo import create_delivery, list_webhooks, update_delivery
from utils.notification_adapters import payload_for_adapter


logger = logging.getLogger(__name__)


def dispatch_event(user_id: int, event: str, payload: dict) -> int:
    delivered = 0
    for webhook in list_webhooks(user_id):
        if webhook["event"] != event and webhook["event"] != "*":
            continue
        delivery_id = create_delivery(webhook["id"], event, payload)
        for attempt in range(1, 4):
            try:
                body = payload_for_adapter(webhook.get("adapter", "generic"), event, payload) if webhook.get("adapter", "generic") != "generic" else {"event": event, "payload": payload}
                response = httpx.post(webhook["url"], json=body, timeout=5)
                response.raise_for_status()
                update_delivery(delivery_id, attempt, "delivered")
                delivered += 1
                break
            except httpx.HTTPError as exc:
                status = "dead_letter" if attempt == 3 else "retrying"
                update_delivery(delivery_id, attempt, status, str(exc))
                if attempt < 3:
                    time.sleep(2 ** (attempt - 1))
                else:
                    logger.warning("Webhook dead-lettered for %s", webhook["url"])
    return delivered