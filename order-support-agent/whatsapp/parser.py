"""Pure function that pulls the sender and text out of a WhatsApp Cloud API webhook payload."""


def extract_message(payload: dict):
    """Return (sender_phone, text) or None when the payload has no text message."""
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
    except (KeyError, IndexError, TypeError):
        return None
    if message.get("type") != "text":
        return None
    return message.get("from"), message.get("text", {}).get("body", "")
