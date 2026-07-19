from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.base import Base

class WorkOrder(Base):
    __tablename__ = "work_order"

    wo_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("task_request.request_id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("asset.asset_id"), nullable=True)
    priority = Column(String)
    status = Column(String, default="open")
    description = Column(String)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)