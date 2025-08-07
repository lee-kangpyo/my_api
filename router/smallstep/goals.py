from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_GOALS
from schemas.smallstep.goals import Goal, GoalCreate, GoalUpdate
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 목표 관리"]
)

@router.post("/goals", response_model=Goal, status_code=status.HTTP_201_CREATED,
             summary="새로운 목표 생성",
             description="""
새로운 목표를 생성합니다.

**기능:**
- 사용자별 목표 설정
- 목표 카테고리 분류
- 목표 달성 기한 설정

**요청 예시:**
```json
{
  "user_id": 1,
  "title": "영어 공부하기",
  "description": "토익 800점 달성하기",
  "category": "학습",
  "target_date": "2024-06-30T00:00:00"
}
```

**응답 예시:**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "영어 공부하기",
  "description": "토익 800점 달성하기",
  "category": "학습",
  "target_date": "2024-06-30T00:00:00",
  "status": "active",
  "progress": 0,
  "created_at": "2024-01-XX",
  "updated_at": "2024-01-XX"
}
```
""")
def create_goal(goal: GoalCreate, db: Session = Depends(get_smallstep_db)):
    """새로운 목표 생성"""
    try:
        db_goal = SMALLSTEP_GOALS(
            USER_ID=goal.user_id,
            TITLE=goal.title,
            DESCRIPTION=goal.description,
            CATEGORY=goal.category,
            TARGET_DATE=goal.target_date
        )
        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        return db_goal
    except Exception as e:
        logger.error(f"Goal creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="목표 생성 중 오류가 발생했습니다.")

@router.get("/goals/user/{user_id}", response_model=List[Goal],
            summary="사용자의 목표 목록 조회",
            description="""
특정 사용자의 모든 목표를 조회합니다.

**기능:**
- 사용자별 목표 목록 조회
- 목표 상태별 필터링 가능
- 진행률 확인

**응답 예시:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "title": "영어 공부하기",
    "description": "토익 800점 달성하기",
    "category": "학습",
    "target_date": "2024-06-30T00:00:00",
    "status": "active",
    "progress": 30,
    "created_at": "2024-01-XX",
    "updated_at": "2024-01-XX"
  }
]
```
""")
def get_user_goals(user_id: int, db: Session = Depends(get_smallstep_db)):
    """사용자의 목표 목록 조회"""
    goals = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.USER_ID == user_id).all()
    return goals

@router.get("/goals/{goal_id}", response_model=Goal,
            summary="목표 상세 조회",
            description="""
특정 목표의 상세 정보를 조회합니다.

**기능:**
- 목표 상세 정보 조회
- 진행 상황 확인
- 관련 활동 목록 확인
""")
def get_goal(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """목표 상세 조회"""
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.ID == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return goal

@router.put("/goals/{goal_id}", response_model=Goal,
            summary="목표 정보 업데이트",
            description="""
목표 정보를 업데이트합니다.

**업데이트 가능한 필드:**
- title: 목표 제목
- description: 목표 설명
- category: 목표 카테고리
- status: 목표 상태 (active, completed, paused)
- progress: 진행률 (0-100)
- target_date: 목표 달성 기한
""")
def update_goal(goal_id: int, goal_update: GoalUpdate, db: Session = Depends(get_smallstep_db)):
    """목표 업데이트"""
    db_goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.ID == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    
    update_data = goal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_goal, field.upper(), value)
    
    db.commit()
    db.refresh(db_goal)
    return db_goal 