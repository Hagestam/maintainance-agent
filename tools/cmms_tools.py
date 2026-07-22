from database.database import SessionLocal
from models.work_order import WorkOrder
from models.asset import Asset
from models.technician import Technician

# Costs ~15 tokens per execution
def create_work_order(priority: str, description: str, asset_id: int = None) -> dict:
    db = SessionLocal()
    new_wo = WorkOrder(
        priority=priority,
        description=description,
        asset_id=asset_id,
        status="open"
    )
    db.add(new_wo)
    db.commit()
    db.refresh(new_wo)
    db.close()

    return {
        "status": "success",
        "wo_id": new_wo.wo_id,
        "priority": new_wo.priority
    }

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