from fastapi import FastAPI
from pydantic import BaseModel
from api.routes import whatsapp_webhook, dashboard
from agents.orchestrator import handle_message

app = FastAPI(title = "RT Knits Maintainance Agent")

app.include_router(whatsapp_webhook.router, prefix = "/webhook")
app.include_router(dashboard.router, prefix = "/api")

# --- Schema for WhatsApp Web Bridge ---
class ChatRequest(BaseModel):
    user: str
    message: str

# --- Endpoint called by bridge.js ---
@app.post("/api/chat")
async def chat_bridge(req: ChatRequest):
    # Pass user & text to your agent and return Claude's response
    reply = handle_message(req.user, req.message)
    return {"reply": reply}

@app.get("/health")
def health():
    return {"status": "ok"}