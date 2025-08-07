from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ActivityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week: int
    day: int
    phase_link: int
    title: str
    description: Optional[str] = None
    activity_type: Optional[str] = None

class ActivityCreate(ActivityBase):
    goal_id: int

class ActivityUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Optional[str] = None
    description: Optional[str] = None
    activity_type: Optional[str] = None
    is_completed: Optional[bool] = None

class Activity(ActivityBase):
    id: int
    goal_id: int
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime 