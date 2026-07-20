import httpx
from app.config import settings


BASE_URL = (
    f"https://graph.facebook.com/v20.0/"
    f"{settings.phone_number_id}/messages"
)


def send_whatsapp(to: str, message: str):

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json"
    }

    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = httpx.post(
            BASE_URL,
            headers=headers,
            json=body,
            timeout=30
        )

        print(f"WhatsApp API status: {response.status_code}")
        print(f"WhatsApp API response: {response.text}")

        response.raise_for_status()

        print(f"[SENT] Message delivered to {to}")

    except httpx.HTTPStatusError as e:
        print(
            f"[ERROR] Failed to send to {to}: "
            f"{e.response.text}"
        )

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")