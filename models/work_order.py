# models/work_order.py
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Boolean, Float
from sqlalchemy.sql import func
from database.base import Base

class WOType(str, enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    PLANNED = "PLANNED"
    REACTIVE = "REACTIVE"

class WorkOrder(Base):
    __tablename__ = "work_order"

    wo_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, nullable=True)
    asset_id = Column(Integer, ForeignKey("asset.asset_id"), nullable=True)
    assigned_tech_id = Column(Integer, ForeignKey("technician.tech_id"), nullable=True)
    priority = Column(String)                          # P0, P1, P2
    status = Column(String, default="open")            # open, in_progress, closed
    type = Column(String, default=WOType.REACTIVE)     # PREVENTIVE, PLANNED, REACTIVE
    source = Column(String, default="reactive")        # Keeps backward compatibility
    description = Column(String)
    photo_url = Column(String, nullable=True)
    scheduled_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)                  # 1 to 5 stars
    feedback_comments = Column(String, nullable=True)
    is_repeat_issue = Column(Boolean, default=False)        # True if asset failed within 14 days
    reward_points = Column(Float, default=0.0)