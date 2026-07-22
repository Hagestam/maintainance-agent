from datetime import date, timedelta
from database.database import SessionLocal
from models.work_order import WorkOrder
from models.technician import Technician
from tools.whatsapp_tools import send_whatsapp
from tools.pm_planner import generate_pm_work_orders  # <--- 1. IMPORT THIS

MAX_JOBS_PER_TECH = 6  # cap per technician per day

def build_nightly_plan() -> dict:
    """
    Runs every evening. For each active technician:
    1. Generate due Preventive Maintenance work orders
    2. Find their open/planned work orders
    3. Assign unassigned P1/P2 work orders to fill their day
    4. Send them their list on WhatsApp
    """
    db = SessionLocal()
    tomorrow = date.today() + timedelta(days=1)
    results = []

    try:
        # Get all technicians currently on shift or active
        technicians = db.query(Technician).filter(
            Technician.on_shift == True,
            Technician.phone_number != None
        ).all()

        if not technicians:
            return {"status": "no_technicians", "sent": 0}

        # -------------------------------------------------------------
        # <--- 2. GENERATE PM WORK ORDERS HERE BEFORE QUERYING POOL --->
        pm_count = generate_pm_work_orders(db, target_date=tomorrow)
        print(f"[PM PLANNER] Generated {pm_count} PM work orders for {tomorrow}")
        # -------------------------------------------------------------

        # Get unassigned planned work orders for tomorrow (includes newly created PMs)
        unassigned = db.query(WorkOrder).filter(
            WorkOrder.status == "open",
            WorkOrder.assigned_tech_id == None,
            WorkOrder.priority.in_(["P1", "P2"])
        ).order_by(WorkOrder.priority, WorkOrder.wo_id).all()

        unassigned_pool = list(unassigned)

        for tech in technicians:
            # Work orders already assigned to this tech (includes pre-assigned PMs)
            already_assigned = db.query(WorkOrder).filter(
                WorkOrder.assigned_tech_id == tech.tech_id,
                WorkOrder.status == "open"
            ).all()

            plan = list(already_assigned)
            slots_left = MAX_JOBS_PER_TECH - len(plan)

            # Fill remaining slots from unassigned pool (trade match preferred)
            remaining_pool = []
            for wo in unassigned_pool:
                if slots_left <= 0:
                    remaining_pool.append(wo)
                    continue

                wo.assigned_tech_id = tech.tech_id
                wo.scheduled_date = tomorrow
                wo.source = "planned"
                plan.append(wo)
                slots_left -= 1

            unassigned_pool = remaining_pool

        db.commit()

        # Now send each technician their plan
        for tech in technicians:
            plan = db.query(WorkOrder).filter(
                WorkOrder.assigned_tech_id == tech.tech_id,
                WorkOrder.status == "open"
            ).order_by(WorkOrder.priority).all()

            if not plan:
                message = (
                    f"Good evening {tech.name} 👋\n\n"
                    f"No planned work orders for tomorrow ({tomorrow}).\n"
                    f"You may be assigned reactive tasks during the shift."
                )
            else:
                lines = [f"Good evening {tech.name} 👋\n"]
                lines.append(f"📋 Your work plan for tomorrow ({tomorrow}):\n")
                for i, wo in enumerate(plan, 1):
                    priority_emoji = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}.get(wo.priority, "⚪")
                    lines.append(
                        f"{i}. {priority_emoji} [{wo.priority}] WO#{wo.wo_id}\n"
                        f"   {wo.description}"
                    )
                lines.append(
                    f"\nTotal: {len(plan)} job(s). "
                    f"New urgent tasks may be added during your shift.\n"
                    f"Reply to this number if you need to report anything."
                )
                message = "\n".join(lines)

            result = send_whatsapp(tech.phone_number, message)
            results.append({
                "tech": tech.name,
                "phone": tech.phone_number,
                "jobs": len(plan),
                "send_status": result.get("status")
            })

    finally:
        db.close()

    sent = sum(1 for r in results if r["send_status"] == "sent")
    return {
        "status": "complete",
        "date": str(tomorrow),
        "technicians_notified": sent,
        "breakdown": results
    }