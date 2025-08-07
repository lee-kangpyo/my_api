from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_GAME_DATA
from schemas.smallstep.game_data import GameData, GameDataCreate, GameDataUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 게임 데이터"]
)

@router.post("/game-data", response_model=GameData, status_code=status.HTTP_201_CREATED,
             summary="새로운 게임 데이터 생성",
             description="""
사용자의 게임 데이터를 생성합니다.

**기능:**
- 사용자별 게임 데이터 초기화
- 레벨 및 경험치 설정
- 연속 성공일 추적

**요청 예시:**
```json
{
  "user_id": 1,
  "level": 1,
  "experience": 0,
  "current_streak": 0,
  "longest_streak": 0
}
```
""")
def create_game_data(game_data: GameDataCreate, db: Session = Depends(get_smallstep_db)):
    """새로운 게임 데이터 생성"""
    try:
        db_game_data = SMALLSTEP_GAME_DATA(
            USER_ID=game_data.user_id,
            LEVEL=game_data.level,
            EXPERIENCE=game_data.experience,
            CURRENT_STREAK=game_data.current_streak,
            LONGEST_STREAK=game_data.longest_streak
        )
        db.add(db_game_data)
        db.commit()
        db.refresh(db_game_data)
        return db_game_data
    except Exception as e:
        logger.error(f"Game data creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="게임 데이터 생성 중 오류가 발생했습니다.")

@router.get("/game-data/user/{user_id}", response_model=GameData,
            summary="사용자의 게임 데이터 조회",
            description="""
사용자의 게임 데이터를 조회합니다.

**기능:**
- 현재 레벨 및 경험치 확인
- 연속 성공일 확인
- 최고 연속 성공일 확인

**응답 예시:**
```json
{
  "id": 1,
  "user_id": 1,
  "level": 5,
  "experience": 1250,
  "current_streak": 7,
  "longest_streak": 12,
  "last_completed_date": "2024-01-XX",
  "created_at": "2024-01-XX",
  "updated_at": "2024-01-XX"
}
```
""")
def get_user_game_data(user_id: int, db: Session = Depends(get_smallstep_db)):
    """사용자의 게임 데이터 조회"""
    game_data = db.query(SMALLSTEP_GAME_DATA).filter(SMALLSTEP_GAME_DATA.USER_ID == user_id).first()
    if not game_data:
        raise HTTPException(status_code=404, detail="게임 데이터를 찾을 수 없습니다.")
    return game_data

@router.put("/game-data/{game_data_id}", response_model=GameData,
            summary="게임 데이터 업데이트",
            description="""
사용자의 게임 데이터를 업데이트합니다.

**업데이트 가능한 필드:**
- level: 현재 레벨
- experience: 경험치
- current_streak: 현재 연속 성공일
- longest_streak: 최고 연속 성공일
- last_completed_date: 마지막 완료 날짜
""")
def update_game_data(game_data_id: int, game_data_update: GameDataUpdate, db: Session = Depends(get_smallstep_db)):
    """게임 데이터 업데이트"""
    db_game_data = db.query(SMALLSTEP_GAME_DATA).filter(SMALLSTEP_GAME_DATA.ID == game_data_id).first()
    if not db_game_data:
        raise HTTPException(status_code=404, detail="게임 데이터를 찾을 수 없습니다.")
    
    update_data = game_data_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_game_data, field.upper(), value)
    
    db.commit()
    db.refresh(db_game_data)
    return db_game_data 