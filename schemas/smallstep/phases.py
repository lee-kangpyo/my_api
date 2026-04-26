from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PhaseStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'

class PhaseBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phase_order: int
    phase_title: str
    phase_description: Optional[str] = None
    estimated_weeks: Optional[int] = None

class PhaseCreate(PhaseBase):
    goal_id: int

class PhaseUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phase_title: Optional[str] = None
    phase_description: Optional[str] = None
    status: Optional[PhaseStatus] = None

class PhaseResponse(PhaseBase):
    id: int
    goal_id: int
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    weekly_plans: Optional[List[dict]] = None

# Forward reference rebuild for Pydantic v2
PhaseResponse.model_rebuild()
