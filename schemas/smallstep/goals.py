from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class GoalType(str, Enum):
    DEADLINE = 'DEADLINE'
    ONGOING = 'ONGOING'

class GoalStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    MAINTAIN = 'MAINTAIN'
    PAUSED = 'PAUSED'
    COMPLETED = 'COMPLETED'
    ARCHIVED = 'ARCHIVED'

class GoalBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    goal_text: str
    goal_type: GoalType = GoalType.ONGOING
    deadline_date: Optional[datetime] = None

class GoalCreate(GoalBase):
    user_id: int

class GoalUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    goal_text: Optional[str] = None
    goal_type: Optional[GoalType] = None
    status: Optional[GoalStatus] = None
    deadline_date: Optional[datetime] = None

class Goal(GoalBase):
    id: int
    user_id: int
    status: GoalStatus = GoalStatus.ACTIVE
    current_level: int = 1
    created_at: datetime
    updated_at: datetime