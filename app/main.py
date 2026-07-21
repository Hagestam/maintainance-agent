from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from api.routes import whatsapp_webhook, dashboard
from agents.orchestrator import handle_message

app = FastAPI(title="RT Knits Maintenance Agent")

app.include_router(whatsapp_webhook.router, prefix="/webhook")
app.include_router(dashboard.router, prefix="/api")

class ChatRequest(BaseModel):
    user: str
    message: str
    image_base64: Optional[str] = None
    image_mime_type: Optional[str] = None

@app.post("/api/chat")
async def chat_bridge(req: ChatRequest):
    reply = handle_message(
        req.user,
        req.message,
        image_base64=req.image_base64,
        image_mime_type=req.image_mime_type
    )
    return {"reply": reply}

@app.get("/health")
def health():
    return {"status": "ok"}