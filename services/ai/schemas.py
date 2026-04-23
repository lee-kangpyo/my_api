"""
AI 응답 Pydantic 스키마 (v2)
Phase 생성 및 주간 계획 생성에 사용되는 AI 응답 모델
"""
from pydantic import BaseModel, Field
from typing import List


# ===== Phase 생성 AI 응답 스키마 =====

class PhaseItem(BaseModel):
    """AI가 생성한 개별 Phase 항목"""
    phase_order: int = Field(..., description="Phase 순서 (1부터 시작)")
    phase_title: str = Field(..., description="Phase 제목 (간결하고 명확하게)")
    phase_description: str = Field(..., description="Phase 설명 (100자 이내)")
    estimated_weeks: int = Field(..., ge=1, le=12, description="예상 소요 주수 (1~12주)")


class PhaseGenerationResponse(BaseModel):
    """AI Phase 생성 응답 (목표 → 2~5개 Phase)"""
    phases: List[PhaseItem] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="생성된 Phase 목록 (2~5개)"
    )


# ===== 주간 계획 생성 AI 응답 스키마 =====

class TaskItem(BaseModel):
    """AI가 생성한 개별 주간 태스크"""
    task_order: int = Field(..., description="태스크 순서 (1부터 시작)")
    task_title: str = Field(..., description="태스크 제목 (간결하게)")
    task_description: str = Field(..., description="태스크 설명 (구체적인 행동 지침)")
    estimated_minutes: int = Field(..., ge=5, le=180, description="예상 소요 시간(분, 5~180분)")


class WeeklyPlanGenerationResponse(BaseModel):
    """AI 주간 계획 생성 응답"""
    tasks: List[TaskItem] = Field(
        ...,
        min_length=3,
        max_length=7,
        description="이번 주 태스크 목록 (3~7개)"
    )
    ai_message: str = Field(
        ...,
        description="사용자에게 보여줄 AI 코멘트 (격려/안내 메시지)"
    )
