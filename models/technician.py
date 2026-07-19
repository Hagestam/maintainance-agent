from sqlalchemy import Column, Integer, String, Boolean
from database.base import Base

class Technician(Base):
    __tablename__ = "technician"

    tech_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    trade = Column(String)
    pool = Column(String)
    phone_number = Column(String)
    on_shift = Column(Boolean, default=False)