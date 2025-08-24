#!/usr/bin/env python3
"""
GGUF + Kiwi 조합 테스트 (ModelManager 사용)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # backend 폴더를 경로에 추가

import json
import numpy as np
from services.model_manager import model_manager

def test_gguf_kiwi_with_manager():
    """ModelManager를 사용한 GGUF + Kiwi 조합 테스트"""
    
    print("🚀 ModelManager를 통한 GGUF + Kiwi 테스트 시작")
    print("=" * 50)
    
    try:
        # ModelManager를 통한 모델 로딩
        print("📊 ModelManager를 통한 모델 준비 중...")
        
        # GGUF 모델 및 Kiwi 분석기 로드
        gguf_model = model_manager.get_gguf_model()
        kiwi = model_manager.get_kiwi_analyzer()
        
        print("✅ 모든 모델 로드 완료!")
        
        # 테스트 텍스트
        test_texts = [
            "3개월 내에 5km 러닝을 30분 내에 완주하기",
            "한 달 안에 영어 면접 완벽 대비하기",
            "파이썬 프로그래밍 기초부터 고급까지 마스터하기"
        ]
        
        print(f"\n📝 테스트 텍스트 ({len(test_texts)}개):")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. {text}")
        
        # Dense 벡터 생성 테스트
        print(f"\n🔄 Dense 벡터 생성 중...")
        embeddings = []
        
        for i, text in enumerate(test_texts):
            print(f"  처리 중: {i+1}/{len(test_texts)}")
            embedding = gguf_model.embed(text)
            embeddings.append(np.array(embedding))
        
        embeddings = np.array(embeddings)
        print(f"✅ Dense 벡터 생성 완료: {embeddings.shape}")
        
        # Kiwi 키워드 추출 테스트
        print(f"\n🥝 Kiwi 키워드 추출 테스트:")
        first_text = test_texts[0]
        
        # 형태소 분석 및 명사 추출
        analyzed = kiwi.analyze(first_text)
        nouns = [token.form for token in analyzed[0][0] if token.tag.startswith('N')]
        
        print(f"\n  텍스트: {first_text}")
        print(f"  명사 추출: {nouns}")
        
        # MariaDB 저장 형태 예시
        print(f"\n💾 MariaDB 저장 형태 예시:")
        dense_for_db = embeddings[0].tolist()
        print(f"  Dense 벡터 길이: {len(dense_for_db)}")
        print(f"  Dense 벡터 차원: {embeddings.shape[1]}")
        
        sparse_for_db = {
            "keywords": ", ".join(nouns),
            "weights": {noun: 1.0 for noun in nouns},
            "extraction_method": "kiwi",
            "total_tokens": len(kiwi.tokenize(first_text))
        }
        print(f"  Sparse JSON 예시:")
        print(json.dumps(sparse_for_db, indent=2, ensure_ascii=False))
        
        # 유사도 테스트
        print(f"\n🎯 유사도 테스트:")
        sim = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        print(f"  '러닝' vs '영어면접' 유사도: {sim:.4f}")
        
        # ModelManager 정보 출력
        print(f"\n📊 ModelManager 정보:")
        model_info = model_manager.get_model_info()
        print(json.dumps(model_info, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 50)
        print("🎉 ModelManager를 통한 테스트 완료!")
        print("✅ Dense 벡터 생성 성공 (GGUF)")
        print("✅ Sparse 키워드 추출 성공 (Kiwi)")
        print("✅ 통합 모델 관리 확인")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        print("🔍 다음을 확인하세요:")
        print("   1. ModelManager가 정상적으로 초기화되었는지")
        print("   2. 필요한 패키지가 모두 설치되었는지")
        print("   3. 충분한 메모리가 있는지")
        return False

if __name__ == "__main__":
    success = test_gguf_kiwi_with_manager()
    if not success:
        exit(1)
