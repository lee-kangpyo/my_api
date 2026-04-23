"""
AI 클라이언트 모듈 (v2)
LiteLLM + Instructor 기반 타입 안전한 AI 클라이언트
"""
import os
import logging
from typing import Type, TypeVar
from pydantic import BaseModel

import instructor
from litellm import completion

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# 환경 변수에서 설정 읽기
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gemini/gemini-1.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Instructor 클라이언트 초기화 (LiteLLM 래핑)
_client = instructor.from_litellm(completion)


def get_ai_client():
    """Instructor 클라이언트 반환"""
    return _client


def call_ai(
    messages: list[dict],
    response_model: Type[T],
    max_retries: int = 3,
) -> T:
    """
    AI 호출 공통 함수
    
    Args:
        messages: OpenAI 형식의 메시지 리스트
        response_model: 응답을 파싱할 Pydantic 모델 클래스
        max_retries: 실패 시 재시도 횟수 (Instructor 내장)
    
    Returns:
        response_model 인스턴스
    """
    try:
        logger.info(f"AI 호출 시작 - 모델: {LITELLM_MODEL}, 응답 타입: {response_model.__name__}")
        
        response = _client.chat.completions.create(
            model=LITELLM_MODEL,
            messages=messages,
            response_model=response_model,
            max_retries=max_retries,
        )
        
        logger.info(f"AI 호출 성공 - 응답 타입: {response_model.__name__}")
        return response
        
    except Exception as e:
        logger.error(f"AI 호출 실패: {e}")
        raise
