from sqlalchemy import Column, Integer, String
from database.base import Base

class Department(Base):
    __tablename__ = "department"
    
    dept_id = Column(Integer, primary_key = True, autoincrement = True)
    name = Column(String, nullable=False)
    location = Column(String)