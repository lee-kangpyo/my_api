from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    LOCKED = 'LOCKED'
    AVAILABLE = 'AVAILABLE'
    COMPLETED = 'COMPLETED'
    SKIPPED = 'SKIPPED'

class TaskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_order: int
    task_title: str
    task_description: Optional[str] = None
    estimated_minutes: Optional[int] = None

class TaskCreate(TaskBase):
    weekly_plan_id: int
    goal_id: int

class TaskUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    id: int
    weekly_plan_id: int
    goal_id: int
    status: TaskStatus = TaskStatus.LOCKED
    completed_at: Optional[datetime] = None
    created_at: datetime
