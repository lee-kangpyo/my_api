#!/usr/bin/env python3
"""
개선된 키워드 추출 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # backend 폴더를 경로에 추가

from services.embedding_service import EmbeddingService

def test_keyword_comparison():
    """기본 vs 개선된 키워드 추출 비교"""
    
    print("🔍 키워드 추출 방식 비교 테스트")
    print("=" * 60)
    
    test_text = "3개월 내에 5km 러닝을 30분 내에 완주하기"
    print(f"📝 테스트 텍스트: {test_text}")
    
    try:
        # 1. 기본 방식
        print(f"\n🔹 기본 방식 (basic_kiwi):")
        basic_service = EmbeddingService(keyword_method="basic_kiwi")
        basic_result = basic_service.extract_sparse_keywords(test_text)
        print(f"   키워드: {basic_result['keywords']}")
        
        # 2. 개선된 방식
        print(f"\n🔸 개선된 방식 (improved_kiwi):")
        improved_service = EmbeddingService(keyword_method="improved_kiwi")
        improved_result = improved_service.extract_sparse_keywords(test_text)
        print(f"   키워드: {improved_result['keywords']}")
        
        # 3. 비교
        print(f"\n📊 비교 결과:")
        basic_keywords = set(basic_result['keywords'].split(', ')) if basic_result['keywords'] else set()
        improved_keywords = set(improved_result['keywords'].split(', ')) if improved_result['keywords'] else set()
        
        print(f"   기본 방식:   {basic_keywords}")
        print(f"   개선된 방식: {improved_keywords}")
        
        new_keywords = improved_keywords - basic_keywords
        if new_keywords:
            print(f"   ✨ 새로 추출된 키워드: {new_keywords}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_keyword_comparison()
    if not success:
        exit(1)
