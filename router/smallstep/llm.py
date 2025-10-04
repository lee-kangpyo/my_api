from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import os
import logging
from prompts.goal_analysis import create_goal_analysis_prompt
from prompts.feedback import create_feedback_prompt
from schemas.smallstep.activities import Activity
from datetime import datetime
from services.filtering import SafetyAPIService, InputValidationService, LLMAnalysisService

logger = logging.getLogger(__name__)

# 서비스 초기화
safety_service = SafetyAPIService()
validation_service = InputValidationService()
llm_analysis_service = LLMAnalysisService()

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - LLM 서비스"]
)

# Google AI 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        # 최신 권장 모델 사용
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        logger.info("Google AI 모델 초기화 성공: gemini-2.0-flash-lite")
    except Exception as e:
        logger.error(f"gemini-2.0-flash-lite 실패: {e}")
        # 대안 모델 시도
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("대안 모델 사용: gemini-2.0-flash")
        except Exception as e2:
            logger.error(f"gemini-2.0-flash도 실패: {e2}")
            # 최후의 수단: 1.5 버전
            try:
                model = genai.GenerativeModel('gemini-1.5-flash-002')
                logger.info("최후 모델 사용: gemini-1.5-flash-002")
            except Exception as e3:
                logger.error(f"모든 모델 실패: {e3}")
                model = None
else:
    logger.warning("GOOGLE_API_KEY가 설정되지 않음")
    model = None

from schemas.smallstep.llm import GoalAnalysisRequest, RoadmapPhase, GoalAnalysisResponse


class AIFeedbackRequest(BaseModel):
    user_id: int
    goal_id: int
    completed_activities: List[str]
    current_progress: float

class AIFeedbackResponse(BaseModel):
    feedback_message: str
    next_steps: List[str]
    motivation_quote: str
    progress_analysis: str

@router.post("/llm/analyze-goal", response_model=GoalAnalysisResponse,
             summary="목표 분석 및 활동 계획 생성",
             description="""
LLM을 사용하여 사용자의 목표를 분석하고 활동 계획을 생성합니다.

**기능:**
- 목표 분석 및 난이도 평가
- 단계별 활동 계획 생성
- 예상 소요 시간 계산
- 동기부여 팁 제공

**요청 예시:**
```json
{
  "goal": "영어 회화",
  "duration_weeks": 6,
  "weekly_frequency": 4
}
```
""")
async def analyze_goal(request: GoalAnalysisRequest, db: Session = Depends(get_smallstep_db)):
    """목표 분석 및 활동 계획 생성"""

    # 1단계: Safety API 유해성 검사
    safety_passed, safety_message, safety_info = safety_service.check_safety(request.goal)
    
    # Safety API 응답 로그 출력
    print(f"Safety API 응답 - 목표: '{request.goal}'")
    print(f"Safety API 응답 - 통과: {safety_passed}, 메시지: {safety_message}")
    print(f"Safety API 응답 - 상세정보: {safety_info}")
    
    # Safety API 결과에 따른 분기
    if not safety_passed:
        # Safety API에서 차단된 경우
        print(f"Safety API 차단: {request.goal} - {safety_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=safety_message
        )
    
    # 2단계: 규칙 기반 검사 (빠른 필터링)
    print(f"2단계 규칙 검사 시작: {request.goal}")
    goal_valid, goal_error = validation_service.validate_goal_input(request.goal)
    if not goal_valid:
        print(f"2단계 규칙 검사 차단: {request.goal} - {goal_error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=goal_error
        )
    print(f"2단계 규칙 검사 통과: {request.goal}")
    
    # 3단계: LLM 심층 분석 (정교한 분석)
    print(f"3단계 LLM 분석 시작: {request.goal}")
    llm_valid, llm_error = llm_analysis_service.analyze_goal_safety(request.goal)
    print(f"DEBUG: llm_valid = {llm_valid}, llm_error = {llm_error}")
    if not llm_valid:
        print(f"3단계 LLM 분석 차단: {request.goal} - {llm_error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=llm_error
        )
    else:
        print(f"3단계 LLM 분석 통과: {request.goal}")
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google AI API 키가 설정되지 않았습니다."
        )
    
    try:
        # 기존 프롬프트 함수 사용
        prompt = create_goal_analysis_prompt(
            goal=request.goal,
            duration_weeks=request.duration_weeks,
            weekly_frequency=request.weekly_frequency
        )
        
        # 단 한 번의 독립적인 API 호출
        response = model.generate_content(prompt)
        
        # JSON 응답 파싱
        try:
            import json
            content = response.text.strip()
            
            # 상세한 디버깅 정보 출력
            print("=" * 80)
            print("🔍 LLM 원본 응답 디버깅")
            print("=" * 80)
            print(f"응답 길이: {len(content)} 문자")
            print(f"응답 내용:\n{content}")
            print("=" * 80)
            
            # 로그에도 기록
            logger.info(f"LLM Response Length: {len(content)}")
            logger.info(f"LLM Response: {content}")
            
            # JSON 부분만 추출 (```json ... ``` 형태일 경우)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
                print(f"📋 JSON 블록 추출 (```json): {start}~{end}")
            elif "```" in content:
                # ```json이 없지만 ```가 있는 경우
                start = content.find("```") + 3
                end = content.find("```", start)
                json_str = content[start:end].strip()
                print(f"📋 JSON 블록 추출 (```): {start}~{end}")
            else:
                json_str = content
                print("📋 전체 응답을 JSON으로 사용")
            
            print(f"추출된 JSON 문자열 길이: {len(json_str)}")
            print(f"추출된 JSON:\n{json_str}")
            print("=" * 80)
            
            # 디버깅을 위해 추출된 JSON 로그 출력
            logger.info(f"Extracted JSON Length: {len(json_str)}")
            logger.info(f"Extracted JSON: {json_str}")
            
            # JSON 문자열 정리 (불필요한 문자 제거)
            original_json_str = json_str
            json_str = json_str.replace('\n', ' ').replace('\r', ' ').strip()
            
            # JSON 주석 제거 (// 로 시작하는 라인)
            import re
            json_str = re.sub(r'\s*//.*?(?=\n|$)', '', json_str)
            
            # 중복된 쉼표 제거
            json_str = re.sub(r',\s*,', ',', json_str)
            
            # 객체/배열 끝의 불필요한 쉼표 제거
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            print(f"정리된 JSON 문자열 길이: {len(json_str)}")
            print(f"정리된 JSON:\n{json_str}")
            print("=" * 80)
            
            # JSON 파싱 시도
            try:
                result = json.loads(json_str)
                print("✅ JSON 파싱 성공!")
                print(f"파싱된 결과 타입: {type(result)}")
                print(f"roadmap 키 존재: {'roadmap' in result}")
                print(f"schedule 키 존재: {'schedule' in result}")
                if 'roadmap' in result:
                    print(f"roadmap 항목 수: {len(result['roadmap'])}")
                if 'schedule' in result:
                    print(f"schedule 항목 수: {len(result['schedule'])}")
                print("=" * 80)
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON 파싱 실패: {str(json_error)}")
                print(f"오류 위치: 라인 {json_error.lineno}, 컬럼 {json_error.colno}")
                print(f"오류 문자: {json_error.pos}")
                
                # 오류 위치 주변 텍스트 출력
                error_pos = json_error.pos
                start_pos = max(0, error_pos - 50)
                end_pos = min(len(json_str), error_pos + 50)
                print(f"오류 주변 텍스트: ...{json_str[start_pos:end_pos]}...")
                print("=" * 80)
                
                # 원본 JSON과 정리된 JSON 비교
                print("🔍 원본 vs 정리된 JSON 비교:")
                print(f"원본 길이: {len(original_json_str)}")
                print(f"정리된 길이: {len(json_str)}")
                print("=" * 80)
                
                raise json_error
            
            # Activity 스키마에 맞게 변환
            activities = []
            for item in result["schedule"]:
                activities.append(Activity(
                    week=item["week"],
                    day=item["day"],
                    phase_link=item["phase_link"],
                    activity_type=item["activity_type"],
                    title=item["title"],
                    description=item["description"],
                    goal_id=0,  # 임시값, 실제로는 goal_id 필요
                    id=0,  # 임시값
                    created_at=datetime.now()  # 현재 시간으로 설정
                ))
            
            return GoalAnalysisResponse(
                roadmap=result["roadmap"],
                schedule=activities
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM 응답 파싱 중 오류가 발생했습니다."
            )
        
    except Exception as e:
        logger.error(f"Goal analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="목표 분석 중 오류가 발생했습니다."
        )

@router.post("/llm/generate-feedback", response_model=AIFeedbackResponse,
             summary="AI 피드백 생성",
             description="""
사용자의 진행 상황을 분석하고 AI 피드백을 생성합니다.

**기능:**
- 진행 상황 분석
- 격려 메시지 생성
- 다음 단계 제안
- 동기부여 명언 제공

**요청 예시:**
```json
{
  "user_id": 1,
  "goal_id": 1,
  "completed_activities": ["영어 단어 50개 외우기", "문법 공부"],
  "current_progress": 30.5
}
```
""")
def generate_feedback(request: AIFeedbackRequest, db: Session = Depends(get_smallstep_db)):
    """AI 피드백 생성"""
    if not model:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google AI API 키가 설정되지 않았습니다."
        )
    
    try:
        # 기존 프롬프트 함수 사용
        prompt = create_feedback_prompt(
            completed_activities=request.completed_activities,
            current_progress=request.current_progress
        )
        
        # 단 한 번의 독립적인 API 호출
        response = model.generate_content(prompt)
        
        # JSON 응답 파싱
        try:
            import json
            content = response.text.strip()
            
            # 디버깅을 위해 실제 응답 로그 출력
            logger.info(f"LLM Response: {content}")
            
            # JSON 부분만 추출 (```json ... ``` 형태일 경우)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            elif "```" in content:
                # ```json이 없지만 ```가 있는 경우
                start = content.find("```") + 3
                end = content.find("```", start)
                json_str = content[start:end].strip()
            else:
                json_str = content
            
            # 디버깅을 위해 추출된 JSON 로그 출력
            logger.info(f"Extracted JSON: {json_str}")
            
            # JSON 문자열 정리 (불필요한 문자 제거)
            json_str = json_str.replace('\n', ' ').replace('\r', ' ').strip()
            
            # JSON 파싱
            result = json.loads(json_str)
            
            return AIFeedbackResponse(
                feedback_message=result["feedback_message"],
                next_steps=result["next_steps"],
                motivation_quote=result["motivation_quote"],
                progress_analysis=result["progress_analysis"]
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM 응답 파싱 중 오류가 발생했습니다."
            )
        
    except Exception as e:
        logger.error(f"Feedback generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="피드백 생성 중 오류가 발생했습니다."
        ) 