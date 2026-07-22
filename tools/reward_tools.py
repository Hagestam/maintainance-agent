# tools/reward_tools.py
from datetime import date, timedelta
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.work_order import WorkOrder
from models.technician import Technician
from tools.whatsapp_tools import send_whatsapp

def check_repeat_issue(db: Session, asset_id: int, current_wo_id: int) -> bool:
    """
    Checks if the same asset had a completed work order closed within the last 14 days.
    """
    if not asset_id:
        return False

    fourteen_days_ago = date.today() - timedelta(days=14)
    recent_wo = db.query(WorkOrder).filter(
        WorkOrder.asset_id == asset_id,
        WorkOrder.wo_id != current_wo_id,
        WorkOrder.status == "closed",
        WorkOrder.closed_at >= fourteen_days_ago
    ).first()

    return recent_wo is not None

def process_feedback_and_score(wo_id: int, rating: int, comments: str = "") -> dict:
    """
    Calculates final reward points based on rating and repeat issue check.
    Gating Rules:
    - 1 or 2 Stars OR Repeat Issue within 14 days -> 0 points (Penalty/Gate)
    - 3 Stars -> 50% Speed Points
    - 4 Stars -> 100% Speed Points
    - 5 Stars -> 120% Speed Points
    """
    db = SessionLocal()
    try:
        wo = db.query(WorkOrder).filter(WorkOrder.wo_id == wo_id).first()
        if not wo:
            return {"status": "error", "message": f"WO #{wo_id} not found."}

        # 1. Record Feedback
        wo.rating = rating
        wo.feedback_comments = comments
        
        # 2. Check for Repeat Issue
        is_repeat = check_repeat_issue(db, wo.asset_id, wo.wo_id)
        wo.is_repeat_issue = is_repeat

        # 3. Calculate Base Speed Points (Dummy baseline or time-delta based)
        base_speed_points = 100.0

        # 4. Apply Quality Gating Logic
        if is_repeat or rating in [1, 2]:
            multiplier = 0.0  # Cobra effect mitigation: zero points for poor quality or quick failure
        elif rating == 3:
            multiplier = 0.5
        elif rating == 4:
            multiplier = 1.0
        elif rating == 5:
            multiplier = 1.2
        else:
            multiplier = 0.0

        final_points = base_speed_points * multiplier
        wo.reward_points = final_points

        # 5. Add points to technician's total
        if wo.assigned_tech_id:
            tech = db.query(Technician).filter(Technician.tech_id == wo.assigned_tech_id).first()
            if tech:
                tech.total_points = getattr(tech, 'total_points', 0.0) + final_points

        db.commit()

        return {
            "status": "success",
            "wo_id": wo_id,
            "rating": rating,
            "is_repeat_issue": is_repeat,
            "reward_points_awarded": final_points
        }

    finally:
        db.close()

def request_requester_feedback(wo_id: int, requester_phone: str) -> dict:
    """
    Sends an automated WhatsApp prompt asking the user to rate the completed job.
    """
    message = (
        f"🛠️ *Work Order #{wo_id} Completed*\n\n"
        f"How would you rate the repair quality on a scale of 1 to 5?\n"
        f"Reply with a number (1 = Poor, 5 = Excellent)."
    )
    return send_whatsapp(requester_phone, message)