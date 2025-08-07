from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_USERS
from schemas.smallstep.users import User, UserCreate, UserUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 사용자 관리"]
)

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, 
             summary="새로운 사용자 생성",
             description="""
새로운 SmallStep 사용자를 생성합니다.

**기능:**
- 사용자 기본 정보 등록
- 초기 레벨 및 게임 데이터 설정
- 연속 성공일 초기화

**요청 예시:**
```json
{
  "name": "홍길동",
  "email": "hong@example.com"
}
```

**응답 예시:**
```json
{
  "id": 1,
  "name": "홍길동",
  "email": "hong@example.com",
  "level": 1,
  "consecutive_days": 0,
  "total_steps": 0,
  "completed_steps": 0,
  "current_goal": null,
  "created_at": "2024-01-XX",
  "updated_at": "2024-01-XX"
}
```
""")
def create_user(user: UserCreate, db: Session = Depends(get_smallstep_db)):
    """새로운 사용자 생성"""
    try:
        db_user = SMALLSTEP_USERS(
            NAME=user.name,
            EMAIL=user.email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="사용자 생성 중 오류가 발생했습니다.")

@router.get("/users/{user_id}", response_model=User,
            summary="사용자 정보 조회",
            description="""
특정 사용자의 상세 정보를 조회합니다.

**기능:**
- 사용자 기본 정보 조회
- 현재 진행 상황 확인
- 레벨 및 성취도 확인

**응답 예시:**
```json
{
  "id": 1,
  "name": "홍길동",
  "email": "hong@example.com",
  "level": 5,
  "consecutive_days": 7,
  "total_steps": 25,
  "completed_steps": 18,
  "current_goal": "영어 공부하기",
  "created_at": "2024-01-XX",
  "updated_at": "2024-01-XX"
}
```
""")
def get_user(user_id: int, db: Session = Depends(get_smallstep_db)):
    """사용자 정보 조회"""
    user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

@router.put("/users/{user_id}", response_model=User,
            summary="사용자 정보 업데이트",
            description="""
사용자 정보를 업데이트합니다.

**업데이트 가능한 필드:**
- name: 사용자 이름
- email: 이메일 주소
- level: 현재 레벨
- consecutive_days: 연속 성공일
- total_steps: 총 스텝 수
- completed_steps: 완료한 스텝 수
- current_goal: 현재 목표

**요청 예시:**
```json
{
  "level": 6,
  "consecutive_days": 8,
  "completed_steps": 20
}
```
""")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_smallstep_db)):
    """사용자 정보 업데이트"""
    db_user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field.upper(), value)
    
    db.commit()
    db.refresh(db_user)
    return db_user 