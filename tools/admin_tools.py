from database.database import SessionLocal
from models.work_order import WorkOrder

# List of WhatsApp IDs that have admin rights
ADMIN_NUMBERS = [
    "263488022798523@lid",
    "2540105067160@c.us",
    "254105067160",
    "2540105067160"
]

def require_admin(func):
    """A decorator to block non-admins from executing certain functions."""
    def wrapper(*args, **kwargs):
        requesting_user = kwargs.get("requesting_user")
        if requesting_user not in ADMIN_NUMBERS:
            return {"status": "error", "message": "Unauthorized. You do not have admin privileges to perform this action."}
        return func(*args, **kwargs)
    return wrapper

@require_admin
def delete_work_order(wo_id: int, requesting_user: str = None) -> dict:
    db = SessionLocal()
    
    wo = db.query(WorkOrder).filter(WorkOrder.wo_id == wo_id).first()
    
    if not wo:
        db.close()
        return {"status": "error", "message": f"Work order {wo_id} not found."}
        
    db.delete(wo)
    db.commit()
    db.close()
    
    return {"status": "success", "message": f"Work order {wo_id} has been permanently deleted."}

@require_admin
def view_all_work_orders(status_filter: str = None, requesting_user: str = None) -> dict:
    """Fetches all work orders, optionally filtered by status."""
    db = SessionLocal()
    
    query = db.query(WorkOrder)
    
    # If the user asks for 'pending' or 'solved' tasks, filter the database query
    if status_filter:
        query = query.filter(WorkOrder.status.ilike(f"%{status_filter}%"))
        
    wos = query.all()
    db.close()
    
    if not wos:
        return {"status": "success", "message": "No work orders found.", "tasks": []}
        
    # Format the data so Claude can read it easily
    task_list = []
    for wo in wos:
        task_list.append({
            "wo_id": wo.wo_id,
            "priority": wo.priority,
            "status": wo.status,
            "description": wo.description
        })
        
    return {"status": "success", "tasks": task_list}