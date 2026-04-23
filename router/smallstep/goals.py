from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_GOALS
from schemas.smallstep.goals import Goal, GoalCreate, GoalUpdate
from services.ai.phase_generator import generate_phases
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 목표 관리"]
)

def _generate_phases_background(goal_id: int, db: Session):
    """백그라운드에서 Phase 생성"""
    try:
        generate_phases(goal_id=goal_id, db=db)
    except Exception as e:
        logger.error(f"Background phase generation failed for goal {goal_id}: {e}")

@router.post("/goals", response_model=Goal, status_code=status.HTTP_201_CREATED,
             summary="새로운 목표 생성 및 Phase 자동 생성",
             description="""
새로운 목표를 생성합니다. (v2 아키텍처)
목표 생성 직후 AI가 백그라운드에서 2~5개의 Phase를 자동 생성합니다.

**요청 예시:**
```json
{
  "user_id": 1,
  "goal_text": "매일 아침 30분 러닝하기",
  "goal_type": "ONGOING",
  "deadline_date": null
}
```
""")
def create_goal(
    goal: GoalCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_smallstep_db)
):
    """새로운 목표 생성"""
    try:
        db_goal = SMALLSTEP_GOALS(
            USER_ID=goal.user_id,
            GOAL_TEXT=goal.goal_text,
            GOAL_TYPE=goal.goal_type,
            DEADLINE_DATE=goal.deadline_date,
            STATUS='ACTIVE',
            CURRENT_LEVEL=1
        )
        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        
        # Phase 생성 백그라운드 작업 등록
        # (DB 세션은 백그라운드 작업에서 자체적으로 관리하거나, 이 세션을 유지해야 하지만
        # 간단히 하기 위해 동기 호출을 백그라운드로 넘깁니다. 
        # 실제 환경에서는 Celery나 별도의 DB 세션 생성이 안전합니다. 
        # MVP 수준이므로 여기서는 현재 세션을 넘기지 않고 ID만 넘겨서 안에서 세션을 열게 하는 것이 좋으나,
        # phase_generator의 서명을 바꾸지 않고 일단 동기로 실행하겠습니다. MVP에서 동기 결정사항 반영)
        
        # Design 문서 Decision: "MVP에서는 동기 호출 (구현 단순)"
        generate_phases(goal_id=db_goal.ID, db=db)
        
        return db_goal
    except Exception as e:
        logger.error(f"Goal creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="목표 생성 중 오류가 발생했습니다.")

@router.get("/goals/user/{user_id}", response_model=List[Goal],
            summary="사용자의 목표 목록 조회")
def get_user_goals(user_id: int, db: Session = Depends(get_smallstep_db)):
    """사용자의 목표 목록 조회"""
    goals = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.USER_ID == user_id).all()
    return goals

@router.get("/goals/{goal_id}", response_model=Goal,
            summary="목표 상세 조회")
def get_goal(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """목표 상세 조회"""
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.ID == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return goal

@router.put("/goals/{goal_id}/status", response_model=Goal,
            summary="목표 상태 업데이트")
def update_goal_status(goal_id: int, goal_update: GoalUpdate, db: Session = Depends(get_smallstep_db)):
    """목표 상태 및 정보 업데이트"""
    db_goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.ID == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    
    update_data = goal_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == 'goal_type':
                db_goal.GOAL_TYPE = value.value
            elif field == 'status':
                db_goal.STATUS = value.value
            else:
                setattr(db_goal, field.upper(), value)
    
    db.commit()
    db.refresh(db_goal)
    return db_goal