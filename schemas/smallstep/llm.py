from pydantic import BaseModel
from typing import List, Optional
from schemas.smallstep.activities import Activity

class GoalAnalysisRequest(BaseModel):
    goal: str  # 필수 입력
    duration_weeks: Optional[int] = None  # 선택 입력
    weekly_frequency: Optional[int] = None  # 선택 입력

class RoadmapPhase(BaseModel):
    phase: int
    phase_title: str
    phase_description: str
    key_milestones: List[str]

class GoalAnalysisResponse(BaseModel):
    roadmap: List[RoadmapPhase]
    schedule: List[Activity] 