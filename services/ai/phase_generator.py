"""
Phase 생성 파이프라인 (v2)
목표 → 2~5개 Phase 자동 생성 및 DB 저장
"""
import logging
from sqlalchemy.orm import Session

from models import SMALLSTEP_GOALS, SMALLSTEP_PHASES
from services.ai.client import call_ai
from services.ai.schemas import PhaseGenerationResponse
from services.ai.prompts import build_phase_generation_messages

logger = logging.getLogger(__name__)


def generate_phases(
    goal_id: int,
    db: Session,
) -> list[SMALLSTEP_PHASES]:
    """
    목표에 대한 Phase를 AI로 생성하고 DB에 저장
    
    Args:
        goal_id: 목표 ID
        db: 데이터베이스 세션
    
    Returns:
        생성된 SMALLSTEP_PHASES 레코드 목록
    
    Raises:
        ValueError: 목표를 찾을 수 없는 경우
        Exception: AI 호출 실패 시
    """
    # 목표 조회
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.id == goal_id).first()
    if not goal:
        raise ValueError(f"목표를 찾을 수 없습니다: goal_id={goal_id}")
    
    # 연관된 사용자 정보 조회
    user = goal.smallstep_users
    daily_available_time = user.daily_available_time if user else None
    
    # 마감일 포맷
    deadline_str = goal.deadline_date.isoformat() if goal.deadline_date else None
    
    logger.info(f"Phase 생성 시작 - goal_id={goal_id}, 목표: {goal.goal_text[:30]}...")
    logger.info(f"AI 호출 시작 - 모델 및 프롬프트 준비 완료")
    
    # 프롬프트 조립
    messages = build_phase_generation_messages(
        goal_text=goal.goal_text,
        goal_type=goal.goal_type or "ONGOING",
        deadline_date=deadline_str,
        daily_available_time=daily_available_time,
        current_level=goal.current_level or 1,
    )
    
    # AI 호출
    logger.info(f"AI 호출 중... messages 길이: {len(messages)}")
    ai_response: PhaseGenerationResponse = call_ai(
        messages=messages,
        response_model=PhaseGenerationResponse,
    )
    logger.info(f"AI 호출 완료")
    
    logger.info(f"Phase 생성 완료 - {len(ai_response.phases)}개 Phase 생성됨")
    
    # DB 저장
    created_phases = []
    for phase_item in ai_response.phases:
        db_phase = SMALLSTEP_PHASES(
            goal_id=goal_id,
            phase_order=phase_item.phase_order,
            phase_title=phase_item.phase_title,
            phase_description=phase_item.phase_description,
            estimated_weeks=phase_item.estimated_weeks,
            status='PENDING',
        )
        db.add(db_phase)
        created_phases.append(db_phase)
    
    # 첫 번째 Phase를 ACTIVE로 설정
    if created_phases:
        created_phases[0].status = 'ACTIVE'
    
    db.commit()
    
    # refresh하여 ID 등 반영
    for phase in created_phases:
        db.refresh(phase)
    
    logger.info(f"Phase DB 저장 완료 - goal_id={goal_id}, {len(created_phases)}개 Phase")
    return created_phases
