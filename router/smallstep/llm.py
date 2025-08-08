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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - LLM 서비스"]
)

# Google AI 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
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
def analyze_goal(request: GoalAnalysisRequest, db: Session = Depends(get_smallstep_db)):
    """목표 분석 및 활동 계획 생성"""
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