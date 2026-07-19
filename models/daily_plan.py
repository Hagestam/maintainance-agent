from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from database.base import Base

class DailyPlan(Base):
    __tablename__ = "daily_plan"

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    tech_id = Column(Integer, ForeignKey("technician.tech_id"), nullable=False)
    plan_date = Column(String)
    items = Column(String)  # JSON string of ordered work order IDs
    sent_at = Column(DateTime, nullable=True)
    confirmed = Column(Boolean, default=False)