from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - LLM 기능"]
)

# v2 아키텍처에서는 Phase 생성 및 주간 계획 생성이 각각
# /goals (POST) 와 /weekly-plans/generate (POST) 로 통합되었습니다.
# 이 라우터는 이전 v1 호환성을 유지하거나 디버그 용도로 남겨둘 수 있습니다.
# 현재는 별도의 엔드포인트가 필요하지 않습니다.
