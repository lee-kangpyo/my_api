#!/usr/bin/env python3
"""
임베딩 서비스 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # backend 폴더를 경로에 추가

import json
from services.embedding_service import EmbeddingService

def test_embedding_service():
    """임베딩 서비스 기능 테스트"""
    
    print("🚀 임베딩 서비스 테스트 시작")
    print("=" * 100)
    
    try:
        # 임베딩 서비스 초기화 (개선된 키워드 추출 사용)
        embedding_service = EmbeddingService(keyword_method="improved_kiwi")
        print("✅ 임베딩 서비스 초기화 완료")
        
        # 테스트 텍스트 (다양한 구체적 키워드 포함)
        test_texts = [
            "3개월 내에 5km 러닝을 30분 내에 완주하기",
            "6개월 동안 10kg 감량하고 체지방률 15% 달성하기", 
            "2주 안에 TOEIC 900점 이상 취득하기",
            "1년 내에 100만원 저축하고 투자 포트폴리오 구성하기",
            "매일 2시간씩 파이썬 공부해서 3개월 후 개발자 되기",
            "주 5회 헬스장에서 1시간 30분 운동하기",
            "한 달에 책 5권 읽고 독서 노트 작성하기",
            "12월까지 토익스피킹 레벨7 달성하기"
        ]
        
        print(f"\n📝 테스트 텍스트: {len(test_texts)}개")
        for i, text in enumerate(test_texts):
            print(f"  {i+1}. {text}")
        
        # 개별 임베딩 테스트
        print(f"\n🔧 개별 임베딩 테스트:")
        first_text = test_texts[0]
        embedding_result = embedding_service.create_hybrid_embedding(first_text)
        
        print(f"  텍스트: {first_text}")
        print(f"  Dense 벡터 차원: {len(embedding_result['dense_vector'])}")
        print(f"  키워드 개수: {len(embedding_result['sparse_data']['weights'])}")
        print(f"  추출된 키워드: {embedding_result['sparse_data']['keywords']}")
        
        # 데이터베이스 형식 변환 테스트
        print(f"\n💾 데이터베이스 형식 변환 테스트:")
        dense_vector, sparse_json, keywords_str = embedding_service.format_for_database(embedding_result)
        
        print(f"  Dense 벡터 길이: {len(dense_vector)}")
        print(f"  Sparse JSON 크기: {len(sparse_json)} 문자")
        print(f"  키워드 문자열: {keywords_str}")
        
        # 배치 임베딩 테스트
        print(f"\n📦 배치 임베딩 테스트:")
        batch_results = embedding_service.create_batch_embeddings(test_texts)
        
        print(f"  처리된 텍스트 수: {len(batch_results)}")
        for i, result in enumerate(batch_results):
            keywords = result['sparse_data']['keywords']
            print(f"  {i+1}. {keywords}")
        
        # 서비스 정보 출력
        print(f"\n📊 서비스 정보:")
        service_info = embedding_service.get_service_info()
        print(json.dumps(service_info, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 50)
        print("🎉 임베딩 서비스 테스트 완료!")
        print("✅ 모든 기능이 정상 작동합니다.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        print("🔍 다음을 확인하세요:")
        print("   1. 필요한 패키지가 모두 설치되었는지")
        print("   2. 모델 파일이 정상적으로 다운로드되었는지")
        print("   3. 충분한 메모리가 있는지")
        return False

if __name__ == "__main__":
    success = test_embedding_service()
    if not success:
        exit(1)
