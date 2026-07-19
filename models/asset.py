from sqlalchemy import Column, Integer, String, ForeignKey
from database.base import Base

class Asset(Base):
    __tablename__ = "asset"
    
    asset_id = Column(Integer, primary_key = True, autoincrement = True)
    name = Column(String, nullable=False)
    category = Column(String)
    dept_id = Column(Integer, ForeignKey("department.dept_id"), nullable = True)