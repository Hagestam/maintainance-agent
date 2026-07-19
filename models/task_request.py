from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.base import Base

class TaskRequest(Base):
    __tablename__ = "task_request"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    requester_id = Column(Integer, ForeignKey("requester.requester_id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("asset.asset_id"), nullable=True)
    raw_text = Column(String)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())