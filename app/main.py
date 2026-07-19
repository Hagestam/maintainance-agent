from fastapi import FastAPI
from api.routes import whatsapp_webhook, dashboard

app = FastAPI(title = "RT Knits Maintainance Agent")

app.include_router(whatsapp_webhook.router, prefix = "/webhook")
app.include_router(dashboard.router, prefix = "/api")

@app.get("/health")
def health():
    return {"status": "ok"}