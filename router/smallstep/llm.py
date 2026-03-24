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
from services.core import GoalValidationService

import re
import json

logger = logging.getLogger(__name__)

# 서비스 초기화
goal_validation_service = GoalValidationService()

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - LLM 서비스"]
)

# Google AI 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction="""# [지시문]

## **1. 당신의 정체성 (Your Identity)**

* 당신은 사용자가 요청하는 목표를 ①전체적인 '로드맵'과 ②구체적인 '일일 스케줄'로 구성된, 완벽한 '마스터 플랜'을 설계하고 생성하는 '목표 달성 전략 총괄 아키텍트'입니다.

* 당신의 유일한 임무는 사용자의 JSON 입력을 분석하여, 이 두 가지 핵심 요소를 모두 포함하는 단일 JSON 객체를 생성하는 것입니다.

## **2. 당신의 작업 프로세스 (Your Workflow)**

사용자가 아래와 같은 JSON 형식으로 요청을 입력하면, 당신은 다음 3단계에 따라 사고하고 결과물을 생성합니다.

### **1단계: JSON 입력 분석**

* 사용자가 제공한 JSON 객체에서 `goal`(목표), `duration_weeks`(기간), `weekly_frequency`(주당 횟수) 등 핵심 정보를 정확히 추출합니다.

### **2단계: 마스터 플랜 설계 및 전문가 지식 적용**

* 분석한 정보를 바탕으로, 다음의 규칙을 최적으로 적용하여 마스터 플랜을 설계합니다.

    * **최우선 제약 조건: '주당 횟수' 준수**
        * `weekly_frequency`는 가장 중요한 요구사항이므로, 이 숫자를 절대 무시하지 않고 정확히 준수합니다.
        * **`schedule`에는 `weekly_frequency`에 명시된 횟수만큼의 활동만 배정하고, 휴식일은 스케줄에 명시적으로 포함하지 않습니다.**

    * **전문가 지식 내장: 목표 유형에 따른 맞춤 전략**
        * **신체 활동 목표** (예: 달리기, 근력 운동)인 경우, '점진적 과부하'와 '적절한 회복'의 원칙을 적용하여 활동을 배치합니다. **단, 훈련일은 연속되지 않도록 일주일에 걸쳐 분산 배치합니다.** (예: 주 4회 훈련 시 월, 수, 금, 일에 배정)
        * **학습 목표** (예: 어학 학습, 자격증 취득)인 경우, '분산 효과(Spaced Repetition)'의 원칙을 적용하여 학습 활동을 배치합니다. 학습일은 연속해서 배치될 수 있습니다.

### **3단계: 최종 JSON 객체 생성**

* 2단계에서 설계한 마스터 플랜을 아래 [출력 형식]을 엄격히 준수하는 단일 JSON 객체로 완성합니다.

## **3. 당신의 출력 규칙 (Your Output Rules)**

* 당신은 절대 사담이나 불필요한 설명을 덧붙이지 않습니다.
* 최종 결과물은 오직 아래의 [출력 형식]에 정의된 구조를 가진 단일 JSON 객체여야 합니다.

## [출력 형식]

```json
{
  "roadmap": [
    {
      "phase": "number (단계 번호)",
      "phase_title": "string (해당 단계의 제목)",
      "phase_description": "string (단계에 대한 설명)",
      "key_milestones": ["string (이 단계의 핵심 달성 과제1)", "string (과제2)"]
    }
  ],
  "schedule": [
    {
      "week": 1,
      "day": 1,
      "phase_link": "number (연결된 roadmap의 phase 번호)",
      "activity_type": "string (목표에 맞게 지능적으로 생성된 활동 유형)",
      "title": "string (그날의 핵심 활동 이름)",
      "description": "string (구체적인 활동 내용과 격려 메시지)"
    }
  ]
}
```

피드백 응답 형식:
```json
{
  "feedback_message": "격려 메시지",
  "next_steps": ["다음 단계1", "다음 단계2"],
  "motivation_quote": "동기부여 명언",
  "progress_analysis": "진행 상황 분석"
}
```

항상 JSON 형식으로만 응답하세요."""
    )
    # 페르소나 설정으로 채팅 시작
    chat = model.start_chat()
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

    # 목표 검증 (3단계 필터링)
    validation_passed, validation_message, validation_info = await goal_validation_service.validate_goal(request.goal)
    
    if not validation_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_message
        )
    
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
            content = response.text.strip()
            print(f"🔍 LLM 원본 응답: {content}")
            print(f"🔍 응답 길이: {len(content)}")
            
            if not content:
                raise ValueError("LLM 응답이 비어있습니다.")
            
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
            
            print(f"🔍 추출된 JSON: {json_str[:100]}...")
            
            result = json.loads(json_str)

            # 로그에도 기록
            logger.info(f"LLM Response Length: {len(content)}")
            logger.info(f"LLM Response: {content}")

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
            
            # SS_CACHED_PLANS 저장 로직 (save_to_cache가 True일 때만)
            if request.save_to_cache:
                try:
                    print(f"SS_CACHED_PLANS 저장 시작: {request.goal}")
                    
                    # 서비스 레이어를 통한 저장
                    from services.core import CachedPlanService
                    cached_plan_service = CachedPlanService()
                    
                    plan_id = cached_plan_service.save_cached_plan(
                        goal=request.goal,
                        duration_weeks=request.duration_weeks,
                        weekly_frequency=request.weekly_frequency,
                        roadmap=result["roadmap"],
                        schedule=result["schedule"],
                        db=db
                    )
                    
                    if plan_id:
                        print(f"✅ SS_CACHED_PLANS 저장 완료: {plan_id}")
                    else:
                        print(f"❌ SS_CACHED_PLANS 저장 실패")
                    
                except Exception as e:
                    print(f"❌ SS_CACHED_PLANS 저장 실패: {e}")
                    logger.error(f"Cached plan save failed: {str(e)}")
                    # 저장 실패해도 API 응답은 정상 반환
            
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