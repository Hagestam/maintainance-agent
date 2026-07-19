from sqlalchemy import Column, Integer, String, ForeignKey
from database.base import Base

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    wo_id = Column(Integer, ForeignKey("work_order.wo_id"), nullable=False)
    rating = Column(Integer)
    comment = Column(String, nullable=True)