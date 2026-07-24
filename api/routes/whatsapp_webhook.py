# api/routes/whatsapp_webhook.py
import logging
from fastapi import APIRouter, Request
from agents.orchestrator import handle_message

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Receives inbound messages from bridge.js.
    Payload shape (all fields from bridge):
        {
            "user":             "26XXXXXXXXX@c.us",
            "message":          "the boiler is leaking",
            "image_base64":     "<base64 string or null>",
            "image_mime_type":  "image/jpeg (or null)",
            "audio_base64":     "<base64 string or null>",
            "audio_mime_type":  "audio/ogg (or null)"
        }
    """
    try:
        body = await request.json()

        from_number: str = body.get("user", "")
        text: str = body.get("message", "")
        image_base64: str | None = body.get("image_base64")
        image_mime_type: str | None = body.get("image_mime_type")
        audio_base64: str | None = body.get("audio_base64")
        audio_mime_type: str | None = body.get("audio_mime_type")

        if not from_number:
            return {"reply": None, "error": "missing 'user' field"}

        reply = handle_message(
            from_number=from_number,
            text=text,
            image_base64=image_base64,
            image_mime_type=image_mime_type,
            audio_base64=audio_base64,
            audio_mime_type=audio_mime_type,
        )

        return {"reply": reply}

    except Exception as exc:
        logger.exception("Webhook handler crashed: %s", exc)
        return {"reply": "Internal server error. Please try again."}