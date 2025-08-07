from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_ACTIVITIES
from schemas.smallstep.activities import Activity, ActivityCreate, ActivityUpdate
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 활동 관리"]
)

@router.post("/activities", response_model=Activity, status_code=status.HTTP_201_CREATED,
             summary="새로운 활동 생성",
             description="""
새로운 활동을 생성합니다.

**기능:**
- 목표별 활동 스케줄링
- 주차별, 일별 활동 관리
- 활동 타입 분류

**요청 예시:**
```json
{
  "goal_id": 1,
  "week": 1,
  "day": 1,
  "phase_link": 1,
  "title": "영어 단어 50개 외우기",
  "description": "기초 영어 단어를 학습합니다",
  "activity_type": "학습"
}
```

**응답 예시:**
```json
{
  "id": 1,
  "goal_id": 1,
  "week": 1,
  "day": 1,
  "phase_link": 1,
  "title": "영어 단어 50개 외우기",
  "description": "기초 영어 단어를 학습합니다",
  "activity_type": "학습",
  "is_completed": false,
  "completed_at": null,
  "created_at": "2024-01-XX"
}
```
""")
def create_activity(activity: ActivityCreate, db: Session = Depends(get_smallstep_db)):
    """새로운 활동 생성"""
    try:
        db_activity = SMALLSTEP_ACTIVITIES(
            GOAL_ID=activity.goal_id,
            WEEK=activity.week,
            DAY=activity.day,
            PHASE_LINK=activity.phase_link,
            TITLE=activity.title,
            DESCRIPTION=activity.description,
            ACTIVITY_TYPE=activity.activity_type
        )
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        return db_activity
    except Exception as e:
        logger.error(f"Activity creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="활동 생성 중 오류가 발생했습니다.")

@router.get("/activities/goal/{goal_id}", response_model=List[Activity],
            summary="목표의 활동 목록 조회",
            description="""
특정 목표의 모든 활동을 조회합니다.

**기능:**
- 목표별 활동 목록 조회
- 완료/미완료 활동 구분
- 주차별, 일별 활동 정렬
""")
def get_goal_activities(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """목표의 활동 목록 조회"""
    activities = db.query(SMALLSTEP_ACTIVITIES).filter(SMALLSTEP_ACTIVITIES.GOAL_ID == goal_id).all()
    return activities

@router.put("/activities/{activity_id}/complete",
            summary="활동 완료 처리",
            description="""
특정 활동을 완료 처리합니다.

**기능:**
- 활동 완료 상태 변경
- 완료 시간 기록
- 경험치 및 레벨 업데이트

**응답 예시:**
```json
{
  "message": "활동이 완료되었습니다.",
  "activity_id": 1
}
```
""")
def complete_activity(activity_id: int, db: Session = Depends(get_smallstep_db)):
    """활동 완료 처리"""
    db_activity = db.query(SMALLSTEP_ACTIVITIES).filter(SMALLSTEP_ACTIVITIES.ID == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="활동을 찾을 수 없습니다.")
    
    db_activity.IS_COMPLETED = True
    db_activity.COMPLETED_AT = datetime.now()
    db.commit()
    
    return {"message": "활동이 완료되었습니다.", "activity_id": activity_id} 