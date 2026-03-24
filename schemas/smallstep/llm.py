from pydantic import BaseModel
from typing import List, Optional
from schemas.smallstep.activities import Activity

class GoalAnalysisRequest(BaseModel):
    goal: str  # 필수 입력
    duration_weeks: Optional[int] = None  # 선택 입력
    weekly_frequency: Optional[int] = None  # 선택 입력
    save_to_cache: Optional[bool] = False  # SS_CACHED_PLANS 저장 여부 (기본값: False)

class RoadmapPhase(BaseModel):
    phase: int
    phase_title: str
    phase_description: str
    key_milestones: List[str]

class GoalAnalysisResponse(BaseModel):
    roadmap: List[RoadmapPhase]
    schedule: List[Activity] 