from database.database import SessionLocal
from models.work_order import WorkOrder

def create_work_order(priority: str, description: str, asset_id: int = None) -> dict:
    db = SessionLocal()
    wo = WorkOrder(
        asset_id=asset_id,
        priority=priority,
        description=description,
        status="open"
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    db.close()
    return {"wo_id": wo.wo_id, "priority": priority, "status": "created"}