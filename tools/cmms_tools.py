# tools/cmms_tools.py
from database.database import SessionLocal
from models.work_order import WorkOrder
from models.asset import Asset
from models.technician import Technician


def create_work_order(
    priority: str,
    description: str,
    asset_id: int = None,
    photo_url: str = None,          # ← NEW: path/URL saved by image_store
) -> dict:
    """
    Create a maintenance work order in the CMMS database.
    photo_url is optional — populated automatically when a technician
    sends a photo alongside (or instead of) a text description.
    """
    db = SessionLocal()
    new_wo = WorkOrder(
        priority=priority,
        description=description,
        asset_id=asset_id,
        status="open",
        photo_url=photo_url,        # ← persisted to DB
    )
    db.add(new_wo)
    db.commit()
    db.refresh(new_wo)
    db.close()

    return {
        "status": "success",
        "wo_id": new_wo.wo_id,
        "priority": new_wo.priority,
        "has_photo": photo_url is not None,
    }


def search_assets(query: str) -> list:
    db = SessionLocal()
    results = (
        db.query(Asset)
        .filter(Asset.name.ilike(f"%{query}%"))
        .limit(5)
        .all()
    )
    db.close()
    return [
        {"asset_id": a.asset_id, "name": a.name, "category": a.category}
        for a in results
    ]


def find_available_technician(trade: str = None) -> dict:
    db = SessionLocal()
    query = db.query(Technician)
    if trade:
        query = query.filter(Technician.trade.ilike(f"%{trade}%"))
    tech = query.first()
    db.close()
    if tech:
        return {"tech_id": tech.tech_id, "name": tech.name, "trade": tech.trade}
    return {"error": "No technician found"}


def get_asset_history(asset_id: int) -> list:
    db = SessionLocal()
    orders = (
        db.query(WorkOrder)
        .filter(WorkOrder.asset_id == asset_id)
        .order_by(WorkOrder.wo_id.desc())
        .limit(5)
        .all()
    )
    db.close()
    return [
        {
            "wo_id": w.wo_id,
            "description": w.description,
            "status": w.status,
            "has_photo": w.photo_url is not None,
        }
        for w in orders
    ]