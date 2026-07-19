import httpx
from app.config import settings

BASE_URL = f"https://graph.facebook.com/v20.0/{settings.phone_number_id}/messages"

def send_whatsapp(to: str, message: str):
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json"
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    r = httpx.post(BASE_URL, headers=headers, json=body)
    r.raise_for_status()
    return r.json()