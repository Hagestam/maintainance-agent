# models/preventive_maintenance.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base

class PreventiveMaintenance(Base):
    __tablename__ = "preventive_maintenance"

    pm_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("asset.asset_id"), nullable=False)
    title = Column(String, nullable=False)                   # e.g., "Monthly Boiler Inspection"
    description = Column(String, nullable=False)             # Standard procedure / checklist
    frequency_days = Column(Integer, nullable=False)         # e.g., 30 for monthly, 7 for weekly
    last_performed = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=False, index=True) # Date when next WO should run
    default_priority = Column(String, default="P2")          # P0, P1, P2
    assigned_tech_id = Column(Integer, ForeignKey("technician.tech_id"), nullable=True)

    # Relationships
    asset = relationship("Asset")
    default_tech = relationship("Technician")