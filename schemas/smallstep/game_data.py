from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class GameDataBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    level: int = 1
    experience: int = 0
    current_streak: int = 0
    longest_streak: int = 0

class GameDataCreate(GameDataBase):
    user_id: int

class GameDataUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    level: Optional[int] = None
    experience: Optional[int] = None
    current_streak: Optional[int] = None
    longest_streak: Optional[int] = None
    last_completed_date: Optional[datetime] = None

class GameData(GameDataBase):
    id: int
    user_id: int
    last_completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime 