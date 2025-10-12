#!/usr/bin/env python3
"""
SS_GOAL_TEMPLATES의 GOAL_TEXT를 기반으로 SS_CACHED_PLANS에 기본 스켈레톤 데이터 생성
PLAN_DATA는 빈 구조로 생성하고, 나중에 LLM으로 채워넣을 예정
"""

import sys
import os
import json
import uuid
from datetime import datetime

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from database import get_smallstep_db
from services.search.embedding_service import EmbeddingService

def create_template_skeletons():
    """템플릿별 기본 스켈레톤 데이터 생성"""
    
    print("🔧 SS_GOAL_TEMPLATES → SS_CACHED_PLANS 스켈레톤 생성")
    print("=" * 60)
    
    # DB 세션 생성
    db_gen = get_smallstep_db()
    db = next(db_gen)
    
    try:
        # 1. 하드코딩된 템플릿 데이터 (목표_템플릿_카테고리별.md 기반)
        print("📋 하드코딩된 템플릿 데이터 로드 중...")
        templates = [
            # 🏃‍♂️ 운동/건강 카테고리
            {"id": 1, "category": "운동/건강", "goal_text": "3개월 내에 5km 러닝을 30분 내에 완주하기", "duration_weeks": 12, "weekly_frequency": 3},
            {"id": 2, "category": "운동/건강", "goal_text": "2개월 내에 푸시업 100개 연속으로 하기", "duration_weeks": 8, "weekly_frequency": 4},
            {"id": 3, "category": "운동/건강", "goal_text": "6주 내에 발끝까지 터치하기", "duration_weeks": 6, "weekly_frequency": 5},
            
            # 📚 어학 학습 카테고리
            {"id": 4, "category": "어학 학습", "goal_text": "3개월 내에 일상 영어 대화 가능하게 하기", "duration_weeks": 12, "weekly_frequency": 4},
            {"id": 5, "category": "어학 학습", "goal_text": "2개월 내에 스페인어 기초 문법과 단어 500개 익히기", "duration_weeks": 8, "weekly_frequency": 5},
            {"id": 6, "category": "어학 학습", "goal_text": "4주 내에 히라가나 46자 완벽하게 읽고 쓰기", "duration_weeks": 4, "weekly_frequency": 6},
            
            # 💰 재테크/투자 카테고리
            {"id": 7, "category": "재테크/투자", "goal_text": "2개월 내에 주식 투자 기초 지식 습득하고 첫 투자하기", "duration_weeks": 8, "weekly_frequency": 2},
            {"id": 8, "category": "재테크/투자", "goal_text": "3개월 내에 월 지출을 20% 줄이고 저축 습관 만들기", "duration_weeks": 12, "weekly_frequency": 3},
            {"id": 9, "category": "재테크/투자", "goal_text": "6개월 내에 월 50만원 부업 수익 만들기", "duration_weeks": 24, "weekly_frequency": 4},
            
            # 🎨 취미/창작 카테고리
            {"id": 10, "category": "취미/창작", "goal_text": "3개월 내에 인물화 그리기 기법 마스터하기", "duration_weeks": 12, "weekly_frequency": 3},
            {"id": 11, "category": "취미/창작", "goal_text": "2개월 내에 10가지 한식 요리법 익히기", "duration_weeks": 8, "weekly_frequency": 2},
            {"id": 12, "category": "취미/창작", "goal_text": "6개월 내에 단편 소설 완성하기", "duration_weeks": 24, "weekly_frequency": 3},
            
            # 💻 기술/개발 카테고리
            {"id": 13, "category": "기술/개발", "goal_text": "3개월 내에 HTML, CSS, JavaScript로 간단한 웹사이트 만들기", "duration_weeks": 12, "weekly_frequency": 4},
            {"id": 14, "category": "기술/개발", "goal_text": "6개월 내에 React Native로 간단한 모바일 앱 만들기", "duration_weeks": 24, "weekly_frequency": 3},
            {"id": 15, "category": "기술/개발", "goal_text": "2개월 내에 Python과 Pandas로 데이터 분석 기초 익히기", "duration_weeks": 8, "weekly_frequency": 4},
            
            # 📖 독서/학습 카테고리
            {"id": 16, "category": "독서/학습", "goal_text": "3개월 내에 월 2권씩 책 읽기 습관 만들기", "duration_weeks": 12, "weekly_frequency": 5},
            {"id": 17, "category": "독서/학습", "goal_text": "2개월 내에 온라인 강의 1개 완강하기", "duration_weeks": 8, "weekly_frequency": 4},
            {"id": 18, "category": "독서/학습", "goal_text": "6개월 내에 영어 원서 1권 완독하기", "duration_weeks": 24, "weekly_frequency": 3},
            
            # 🎯 자기계발 카테고리
            {"id": 19, "category": "자기계발", "goal_text": "1개월 내에 시간 관리 앱으로 일정 관리 체계화하기", "duration_weeks": 4, "weekly_frequency": 7},
            {"id": 20, "category": "자기계발", "goal_text": "2개월 내에 매일 10분 명상 습관 만들기", "duration_weeks": 8, "weekly_frequency": 7},
            {"id": 21, "category": "자기계발", "goal_text": "3개월 내에 연간 목표 계획 수립하고 분기별 점검하기", "duration_weeks": 12, "weekly_frequency": 1},
            
            # 🏠 생활/취미 카테고리
            {"id": 22, "category": "생활/취미", "goal_text": "3개월 내에 정원 가꾸기 기초 익히기", "duration_weeks": 12, "weekly_frequency": 2},
            {"id": 23, "category": "생활/취미", "goal_text": "2개월 내에 사진 촬영 기법 마스터하기", "duration_weeks": 8, "weekly_frequency": 3},
            {"id": 24, "category": "생활/취미", "goal_text": "6개월 내에 악기 연주 기초 익히기", "duration_weeks": 24, "weekly_frequency": 4},
            
            # 🎮 게임/엔터테인먼트 카테고리
            {"id": 25, "category": "게임/엔터테인먼트", "goal_text": "3개월 내에 보드게임 마스터하기", "duration_weeks": 12, "weekly_frequency": 2},
            {"id": 26, "category": "게임/엔터테인먼트", "goal_text": "2개월 내에 온라인 게임 고수 되기", "duration_weeks": 8, "weekly_frequency": 5},
            {"id": 27, "category": "게임/엔터테인먼트", "goal_text": "6개월 내에 게임 개발 기초 익히기", "duration_weeks": 24, "weekly_frequency": 3},
        ]
        
        print(f"   총 {len(templates)}개 템플릿 로드됨")
        
        # 2. 임베딩 서비스 초기화
        print("🤖 임베딩 서비스 초기화...")
        embedding_service = EmbeddingService()
        
        # 3. 각 템플릿에 대해 스켈레톤 생성
        created_plans = []
        
        for i, template in enumerate(templates, 1):
            print(f"\n   {i}. [{template['category']}] {template['goal_text'][:40]}...")
            
            try:
                # 하이브리드 임베딩 생성
                print("      🔄 임베딩 생성 중...")
                hybrid_embedding = embedding_service.create_hybrid_embedding(template['goal_text'])
                
                # 벡터를 MariaDB VECTOR 형식으로 변환
                dense_vector = hybrid_embedding['dense_vector']
                if hasattr(dense_vector, 'tolist'):
                    vector_str = f"[{','.join(map(str, dense_vector.tolist()))}]"
                else:
                    vector_str = f"[{','.join(map(str, dense_vector))}]"
                
                # UUID 생성
                plan_id = str(uuid.uuid4())
                
                # 기본 스켈레톤 PLAN_DATA 생성 (roadmap, schedule 제외)
                skeleton_plan_data = {
                    "goal": template['goal_text'],
                    "category": template['category'],
                    "template_id": template['id'],
                    "created_at": datetime.now().isoformat(),
                    "status": "skeleton",  # 스켈레톤 상태 표시
                    "needs_llm_completion": True  # LLM 완성 필요 표시
                }
                
                # sparse_data에서 키워드 추출
                sparse_data = hybrid_embedding['sparse_data']
                keywords = sparse_data.get('keywords', [])
                
                # 데이터 삽입 (새 컬럼 포함)
                insert_query = text("""
                    INSERT INTO SS_CACHED_PLANS 
                    (ID, PLAN_DATA, PLAN_VECTOR, PLAN_SPARSE_VECTOR, SPARSE_KEYWORDS, DURATION_WEEKS, WEEKLY_FREQUENCY, CREATED_AT)
                    VALUES 
                    (:id, :plan_data, VEC_FromText(:plan_vector), :sparse_vector, :sparse_keywords, :duration_weeks, :weekly_frequency, :created_at)
                """)
                
                db.execute(insert_query, {
                    'id': plan_id,
                    'plan_data': json.dumps(skeleton_plan_data, ensure_ascii=False),
                    'plan_vector': vector_str,
                    'sparse_vector': json.dumps(sparse_data, ensure_ascii=False),
                    'sparse_keywords': json.dumps(keywords, ensure_ascii=False),
                    'duration_weeks': template['duration_weeks'],  # 하드코딩된 값 사용
                    'weekly_frequency': template['weekly_frequency'],  # 하드코딩된 값 사용
                    'created_at': datetime.now()
                })
                
                # 생성된 계획 정보 저장
                created_plans.append({
                    'template_id': template['id'],
                    'plan_id': plan_id,
                    'goal_text': template['goal_text'],
                    'category': template['category']
                })
                
                print(f"      ✅ 스켈레톤 생성 완료 (ID: {plan_id[:8]}...)")
                
            except Exception as e:
                print(f"      ❌ 실패: {e}")
                continue
        
        # 4. 커밋
        db.commit()
        print(f"\n💾 데이터베이스 커밋 완료")
        
        # 5. 결과 확인
        print(f"\n📊 생성 결과:")
        print(f"   총 {len(created_plans)}개 스켈레톤 생성됨")
        
        # 6. 연결을 위한 정보 출력
        print(f"\n🔗 템플릿-계획 연결 정보:")
        for plan in created_plans:
            print(f"   템플릿 ID {plan['template_id']} → 계획 ID {plan['plan_id']}")
            print(f"   목표: {plan['goal_text'][:50]}...")
            print(f"   카테고리: {plan['category']}")
            print()
        
        # 7. 연결 SQL 생성
        print("🔗 연결 SQL 생성:")
        print("-- SS_GOAL_TEMPLATES와 SS_CACHED_PLANS 연결")
        for plan in created_plans:
            print(f"UPDATE SS_GOAL_TEMPLATES SET CACHED_PLAN_ID = '{plan['plan_id']}' WHERE ID = {plan['template_id']};")
        
        return created_plans
        
    except Exception as e:
        print(f"❌ 전체 오류: {e}")
        db.rollback()
        return []
    
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 템플릿 스켈레톤 생성 시작")
    plans = create_template_skeletons()
    if plans:
        print(f"\n🎉 {len(plans)}개 스켈레톤 생성 완료!")
        print("이제 LLM으로 PLAN_DATA를 채워넣을 수 있습니다.")
    else:
        print("💥 스켈레톤 생성 실패")
