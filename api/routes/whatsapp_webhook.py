from fastapi import APIRouter, Request, Response
from app.config import settings
from agents.orchestrator import handle_message

router = APIRouter()

@router.get("")
def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

@router.post("")
async def receive(request: Request):
    payload = await request.json()

    print("Received webhook payload:")
    print(payload)

    try:
        entry = payload["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]

        from_number = message["from"]
        msg_type = message.get("type")

        if msg_type == "text":
            text = message["text"]["body"]

            print(f"Message from {from_number}: {text}")

            handle_message(from_number, text)

    except (KeyError, IndexError) as error:
        print(f"Webhook parsing error: {error}")

    return {"status": "received"}