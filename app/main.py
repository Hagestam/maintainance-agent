from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta

from database.database import SessionLocal
from api.routes import whatsapp_webhook, dashboard
from agents.orchestrator import handle_message
from tools.scheduler import start_scheduler, stop_scheduler
from tools.planning_tools import build_nightly_plan
from api.routes.whatsapp_webhook import router as whatsapp_router


# --- Imported Tools for Testing ---
from tools.pm_planner import generate_pm_work_orders
from tools.dispatch_tools import assign_p0_emergency
from tools.reward_tools import process_feedback_and_score

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()   # starts when server boots
    yield
    stop_scheduler()    # clean shutdown

app = FastAPI(title="RT Knits Maintenance Agent", lifespan=lifespan)

app.include_router(whatsapp_webhook.router, prefix="/webhook")
app.include_router(dashboard.router, prefix="/api")
app.include_router(whatsapp_router)

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

# ==========================================
# 🧪 TEST HARNESS ROUTER (For Swagger UI)
# ==========================================
test_router = APIRouter(prefix="/test", tags=["System Tests"])

@test_router.post("/1-generate-pms")
def test_pm_generation():
    """Manually triggers the materialization of PMs due tomorrow."""
    db = SessionLocal()
    tomorrow = date.today() + timedelta(days=1)
    count = generate_pm_work_orders(db, tomorrow)
    db.close()
    return {"message": f"Generated {count} PMs for {tomorrow}"}

# Your existing manual trigger, now properly tagged for Swagger testing
@app.post("/api/trigger-planning", tags=["System Tests"])
def trigger_planning():
    """Runs the nightly dispatch algorithm immediately."""
    result = build_nightly_plan()
    return result

@test_router.post("/3-p0-interrupt")
def test_p0_interrupt(p0_wo_id: int, tech_id: int):
    """Assigns an emergency P0 to a tech and bumps their lowest priority job."""
    result = assign_p0_emergency(p0_wo_id, tech_id)
    return result

@test_router.post("/4-feedback-gate")
def test_feedback_gating(wo_id: int, rating: int):
    """Tests the Cobra Effect mitigation logic."""
    result = process_feedback_and_score(wo_id, rating, "Test feedback")
    return result

# Mount the test router to the main app
app.include_router(test_router)