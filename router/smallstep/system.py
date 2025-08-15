from fastapi import APIRouter
from database import get_smallstep_db, get_db
from datetime import datetime
from sqlalchemy import text

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 시스템"]
)

@router.get("/health",
            summary="SmallStep API 헬스체크",
            description="""
SmallStep API 서버의 상태를 확인합니다.

**기능:**
- API 서버 상태 확인
- SmallStep 데이터베이스 연결 상태 확인
- 로또 앱 데이터베이스 연결 상태 확인
- 서비스 가용성 체크
- 모니터링용 엔드포인트

**응답 예시:**
```json
{
  "status": "healthy",
  "service": "SmallStep API",
  "timestamp": "2025-08-07T17:30:00",
  "databases": {
    "smallstep": "connected",
    "lotto": "connected"
  }
}
```
""")
def health_check():
    """SmallStep API 헬스체크"""
    health_status = {
        "status": "healthy",
        "service": "SmallStep API",
        "timestamp": datetime.now().isoformat(),
        "databases": {}
    }
    
    # SmallStep DB 연결 상태 확인
    try:
        db = next(get_smallstep_db())
        db.execute(text("SELECT 1"))
        db.close()
        health_status["databases"]["smallstep"] = "connected"
    except Exception as e:
        health_status["databases"]["smallstep"] = "disconnected"
        health_status["status"] = "unhealthy"
        health_status["error"] = f"SmallStep DB: {str(e)}"
    
    # 로또 앱 DB 연결 상태 확인
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        health_status["databases"]["lotto"] = "connected"
    except Exception as e:
        health_status["databases"]["lotto"] = "disconnected"
        health_status["status"] = "unhealthy"
        if "error" in health_status:
            health_status["error"] += f" | Lotto DB: {str(e)}"
        else:
            health_status["error"] = f"Lotto DB: {str(e)}"
    
    return health_status 