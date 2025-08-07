from fastapi import APIRouter

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
- 서비스 가용성 체크
- 모니터링용 엔드포인트

**응답 예시:**
```json
{
  "status": "healthy",
  "service": "SmallStep API"
}
```
""")
def health_check():
    """SmallStep API 헬스체크"""
    return {"status": "healthy", "service": "SmallStep API"} 