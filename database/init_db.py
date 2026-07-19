from database.database import engine
from database.base import Base

# Import every model so Base knows about them
from models.department import Department
from models.asset import Asset
from models.technician import Technician
from models.requester import Requester
from models.task_request import TaskRequest
from models.work_order import WorkOrder
from models.assignment import Assignment
from models.feedback import Feedback
from models.daily_plan import DailyPlan

Base.metadata.create_all(bind=engine)
print("All tables created.")