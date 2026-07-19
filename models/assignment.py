from sqlalchemy import Column, Integer, ForeignKey, DateTime
from database.base import Base

class Assignment(Base):
    __tablename__ = "assignment"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    wo_id = Column(Integer, ForeignKey("work_order.wo_id"), nullable=False)
    tech_id = Column(Integer, ForeignKey("technician.tech_id"), nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)