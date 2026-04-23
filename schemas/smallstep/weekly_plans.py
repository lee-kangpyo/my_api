from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class WeeklyPlanBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week_start_date: datetime
    week_end_date: datetime

class WeeklyPlanCreate(WeeklyPlanBase):
    goal_id: int
    phase_id: int
    ai_context: Optional[Dict[str, Any]] = None
    ai_response: Optional[Dict[str, Any]] = None

class WeeklyPlanResponse(WeeklyPlanBase):
    id: int
    goal_id: int
    phase_id: int
    ai_context: Optional[Dict[str, Any]] = None
    ai_response: Optional[Dict[str, Any]] = None
    created_at: datetime
