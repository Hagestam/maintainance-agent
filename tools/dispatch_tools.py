# tools/dispatch_tools.py
from datetime import date, timedelta
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.work_order import WorkOrder, WOType
from models.technician import Technician
from tools.whatsapp_tools import send_whatsapp

MAX_JOBS_PER_TECH = 6

def assign_p0_emergency(p0_wo_id: int, tech_id: int) -> dict:
    """
    Assigns an urgent P0 work order mid-shift to a technician.
    If the tech is at capacity, bumps their lowest priority open task to tomorrow.
    Sends an immediate WhatsApp alert to the technician.
    """
    db = SessionLocal()
    today = date.today()
    tomorrow = today + timedelta(days=1)

    try:
        # 1. Fetch Work Order and Technician
        p0_wo = db.query(WorkOrder).filter(WorkOrder.wo_id == p0_wo_id).first()
        tech = db.query(Technician).filter(Technician.tech_id == tech_id).first()

        if not p0_wo:
            return {"status": "error", "message": f"Work order #{p0_wo_id} not found."}
        if not tech:
            return {"status": "error", "message": f"Technician #{tech_id} not found."}

        # Ensure WO is P0
        p0_wo.priority = "P0"

        # 2. Get tech's current open jobs scheduled for today
        tech_jobs = db.query(WorkOrder).filter(
            WorkOrder.assigned_tech_id == tech.tech_id,
            WorkOrder.status == "open",
            WorkOrder.scheduled_date == today
        ).all()

        bumped_wo = None

        # 3. Interrupt Logic: If capacity reached, bump lowest priority task
        if len(tech_jobs) >= MAX_JOBS_PER_TECH:
            # Priority order for bumping (P2 / Preventive first, then P1)
            # Sort jobs so P2 / PREVENTIVE items appear at the top
            def bump_score(wo: WorkOrder):
                if wo.type == WOType.PREVENTIVE or wo.priority == "P2":
                    return 0
                elif wo.priority == "P1":
                    return 1
                return 2  # Don't bump P0

            candidates = sorted(
                [w for w in tech_jobs if w.priority != "P0"],
                key=bump_score
            )

            if candidates:
                bumped_wo = candidates[0]
                # Bump task to tomorrow
                bumped_wo.scheduled_date = tomorrow
                # Optional: clear assigned_tech_id if you want it re-pooled
                # bumped_wo.assigned_tech_id = None 

        # 4. Assign the P0 Emergency to Tech
        p0_wo.assigned_tech_id = tech.tech_id
        p0_wo.scheduled_date = today
        p0_wo.status = "open"
        p0_wo.source = "reactive"
        p0_wo.type = WOType.REACTIVE

        db.commit()

        # 5. Draft Immediate WhatsApp Dispatch Message
        message_lines = [
            f"🚨 *EMERGENCY DISPATCH (P0)* 🚨\n",
            f"*WO #{p0_wo.wo_id}:* {p0_wo.description}",
            f" *Assigned Immediately to You*"
        ]

        if bumped_wo:
            bump_type = f"[{bumped_wo.type}]" if bumped_wo.type == WOType.PREVENTIVE else f"[{bumped_wo.priority}]"
            message_lines.append(
                f"\n *Schedule Adjustment:* Your WO #{bumped_wo.wo_id} {bump_type} "
                f"(\"{bumped_wo.description}\") has been bumped to tomorrow ({tomorrow}) to accommodate this emergency."
            )

        message_lines.append("\nPlease acknowledge receipt and proceed immediately.")
        message = "\n".join(message_lines)

        # 6. Send Alert via WhatsApp
        dispatch_res = send_whatsapp(tech.phone_number, message)

        return {
            "status": "success",
            "p0_wo_id": p0_wo.wo_id,
            "assigned_to": tech.name,
            "bumped_wo_id": bumped_wo.wo_id if bumped_wo else None,
            "whatsapp_status": dispatch_res.get("status")
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()