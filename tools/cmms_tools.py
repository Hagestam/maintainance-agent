from database.database import SessionLocal
from models.work_order import WorkOrder
from models.asset import Asset
from models.technician import Technician

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

def search_assets(query: str) -> list:
    db = SessionLocal()
    results = db.query(Asset).filter(
        Asset.name.ilike(f"%{query}%")
    ).limit(5).all()
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
    orders = db.query(WorkOrder).filter(
        WorkOrder.asset_id == asset_id
    ).order_by(WorkOrder.wo_id.desc()).limit(5).all()
    db.close()
    return [
        {"wo_id": w.wo_id, "description": w.description, "status": w.status}
        for w in orders
    ]