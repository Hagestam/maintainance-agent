from sqlalchemy import Column, Integer, String, ForeignKey
from database.base import Base

class Requester(Base):
    __tablename__ = "requester"

    requester_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    phone_number = Column(String, nullable=False)
    dept_id = Column(Integer, ForeignKey("department.dept_id"), nullable=True)