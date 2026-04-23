from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_PHASES, SMALLSTEP_GOALS
from schemas.smallstep.phases import PhaseResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - Phase 관리"]
)

@router.get("/goals/{goal_id}/phases", response_model=List[PhaseResponse],
            summary="목표의 Phase 목록 조회")
def get_goal_phases(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """특정 목표의 전체 Phase 목록을 순서대로 조회합니다."""
    # 목표 존재 여부 확인
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.ID == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")

    phases = (
        db.query(SMALLSTEP_PHASES)
        .filter(SMALLSTEP_PHASES.GOAL_ID == goal_id)
        .order_by(SMALLSTEP_PHASES.PHASE_ORDER)
        .all()
    )
    return phases

@router.get("/phases/{phase_id}", response_model=PhaseResponse,
            summary="Phase 상세 조회")
def get_phase(phase_id: int, db: Session = Depends(get_smallstep_db)):
    """특정 Phase의 상세 정보를 조회합니다."""
    phase = db.query(SMALLSTEP_PHASES).filter(SMALLSTEP_PHASES.ID == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase를 찾을 수 없습니다.")
    return phase
