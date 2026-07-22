# tools/pm_planner.py
from datetime import date
from sqlalchemy.orm import Session
from models.preventive_maintenance import PreventiveMaintenance
from models.work_order import WorkOrder, WOType

def generate_pm_work_orders(db: Session, target_date: date) -> int:
    """
    Finds all PM rules due on or before `target_date` and generates 
    open PREVENTIVE WorkOrders matching your database schema.
    """
    due_pms = db.query(PreventiveMaintenance).filter(
        PreventiveMaintenance.next_due_date <= target_date
    ).all()

    created_count = 0

    for pm in due_pms:
        # Check if an open/in-progress PM work order already exists for this asset on target date
        existing_wo = db.query(WorkOrder).filter(
            WorkOrder.asset_id == pm.asset_id,
            WorkOrder.type == WOType.PREVENTIVE,
            WorkOrder.status.in_(["open", "in_progress"]),
            WorkOrder.scheduled_date == target_date
        ).first()

        if not existing_wo:
            # Create the Work Order with full type safety
            new_wo = WorkOrder(
                asset_id=pm.asset_id,
                description=f"[PM] {pm.title}: {pm.description}",
                priority=pm.default_priority,
                status="open",
                type=WOType.PREVENTIVE,
                source="preventive",
                assigned_tech_id=pm.assigned_tech_id,
                scheduled_date=target_date
            )
            db.add(new_wo)
            created_count += 1

    db.commit()
    return created_count