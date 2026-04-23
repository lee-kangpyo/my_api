from pydantic import BaseModel
from typing import List, Optional
from .activities import Activity


class GoalAnalysisRequest(BaseModel):
    goal: str
    duration_weeks: Optional[int] = None
    weekly_frequency: Optional[int] = None

class RoadmapPhase(BaseModel):
    phase: int
    phase_title: str
    phase_description: str
    key_milestones: List[str]

class GoalAnalysisResponse(BaseModel):
    roadmap: List[RoadmapPhase]
    schedule: List[Activity] 