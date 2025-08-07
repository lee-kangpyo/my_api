from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class GoalBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[datetime] = None

class GoalCreate(GoalBase):
    user_id: int

class GoalUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    target_date: Optional[datetime] = None

class Goal(GoalBase):
    id: int
    user_id: int
    status: str = 'active'
    progress: int = 0
    created_at: datetime
    updated_at: datetime 