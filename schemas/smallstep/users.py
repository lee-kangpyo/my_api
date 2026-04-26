from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: Optional[str] = None
    daily_available_time: Optional[int] = None
    notification_enabled: Optional[bool] = True
    notification_time: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str] = None
    email: Optional[str] = None
    daily_available_time: Optional[int] = None
    notification_enabled: Optional[bool] = None
    notification_time: Optional[str] = None

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: int = 1
    experience_points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    created_at: datetime
    updated_at: datetime