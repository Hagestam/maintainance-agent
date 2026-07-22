from fastapi import APIRouter
from database.database import SessionLocal
from models.work_order import WorkOrder
from models.technician import Technician
from models.asset import Asset

router = APIRouter()

@router.get("/workorders")
def list_work_orders(status: str = None, priority: str = None):
    db = SessionLocal()
    query = db.query(WorkOrder)
    if status:
        query = query.filter(WorkOrder.status == status)
    if priority:
        query = query.filter(WorkOrder.priority == priority)
    results = query.order_by(WorkOrder.wo_id.desc()).limit(50).all()
    db.close()
    return [
        {
            "wo_id": w.wo_id,
            "priority": w.priority,
            "status": w.status,
            "description": w.description,
            "asset_id": w.asset_id,
            "created_at": str(w.created_at)
        }
        for w in results
    ]

@router.get("/technicians")
def list_technicians():
    db = SessionLocal()
    techs = db.query(Technician).all()
    db.close()
    return [
        {"tech_id": t.tech_id, "name": t.name, "trade": t.trade, "on_shift": t.on_shift}
        for t in techs
    ]

@router.get("/assets")
def list_assets():
    db = SessionLocal()
    assets = db.query(Asset).all()
    db.close()
    return [
        {"asset_id": a.asset_id, "name": a.name, "category": a.category}
        for a in assets
    ]

@router.get("/stats")
def get_stats():
    db = SessionLocal()
    total = db.query(WorkOrder).count()
    p0 = db.query(WorkOrder).filter(WorkOrder.priority == "P0").count()
    p1 = db.query(WorkOrder).filter(WorkOrder.priority == "P1").count()
    p2 = db.query(WorkOrder).filter(WorkOrder.priority == "P2").count()
    open_count = db.query(WorkOrder).filter(WorkOrder.status != "completed").count()
    db.close()
    return {
        "total_work_orders": total,
        "p0_count": p0,
        "p1_count": p1,
        "p2_count": p2,
        "open_jobs": open_count
    }