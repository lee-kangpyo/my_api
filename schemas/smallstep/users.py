from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str] = None
    email: Optional[str] = None
    level: Optional[int] = None
    consecutive_days: Optional[int] = None
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None
    current_goal: Optional[str] = None

class User(UserBase):
    id: int
    level: int = 1
    consecutive_days: int = 0
    total_steps: int = 0
    completed_steps: int = 0
    current_goal: Optional[str] = None
    created_at: datetime
    updated_at: datetime 