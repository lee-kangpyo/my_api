#!/usr/bin/env python3
"""
GGUF + Kiwi 조합 테스트
"""

import os
import json
import numpy as np
from llama_cpp import Llama
from huggingface_hub import model_info, hf_hub_download
from kiwipiepy import Kiwi

def test_gguf_kiwi():
    """GGUF + Kiwi 조합 테스트"""
    
    print("🚀 GGUF + Kiwi 조합 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. GGUF 모델 준비
        model_repo = 'puppyM/bge-m3-Q4_K_M-GGUF'
        model_filename = 'bge-m3-q4_k_m.gguf'
        
        print("📊 GGUF 모델 준비 중...")
        model_path = hf_hub_download(
            repo_id=model_repo,
            filename=model_filename,
            cache_dir="./models"
        )
        
        gguf_model = Llama(
            model_path=model_path,
            embedding=True,
            verbose=False,
            n_ctx=512,
            n_threads=4
        )
        print("✅ GGUF 모델 로드 완료!")
        
        # 2. Kiwi 형태소 분석기 준비
        print("🥝 Kiwi 형태소 분석기 로드 중...")
        kiwi = Kiwi()
        print("✅ Kiwi 로드 완료!")
        
        # 3. 테스트 텍스트
        test_texts = [
            "3개월 내에 5km 러닝을 30분 내에 완주하기",
            "한 달 안에 영어 면접 완벽 대비하기",
            "파이썬 프로그래밍 기초부터 고급까지 마스터하기"
        ]
        
        print(f"\n📝 테스트 텍스트 ({len(test_texts)}개):")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. {text}")
        
        # 4. Dense 벡터 생성 (GGUF)
        print(f"\n🔄 Dense 벡터 생성 중...")
        embeddings = []
        for i, text in enumerate(test_texts):
            print(f"  처리 중: {i+1}/{len(test_texts)}")
            embedding = gguf_model.create_embedding(text)
            embeddings.append(embedding['data'][0]['embedding'])
        
        embeddings = np.array(embeddings)
        print(f"✅ Dense 벡터 생성 완료: {embeddings.shape}")
        
        # 5. Sparse 키워드 추출 (Kiwi)
        print(f"\n🥝 Kiwi 키워드 추출 테스트:")
        
        for i, text in enumerate(test_texts):
            print(f"\n  텍스트 {i+1}: {text}")
            
            # 명사 추출
            result = kiwi.analyze(text)
            nouns = [token.form for token in result[0][0] if token.tag.startswith('N')]
            print(f"  명사: {nouns}")
            
            # 간단한 토큰화
            tokens = kiwi.tokenize(text)
            meaningful_tokens = [token.form for token in tokens if len(token.form) > 1]
            print(f"  의미있는 토큰: {meaningful_tokens[:8]}")
            
            if i == 0:  # 첫 번째만 자세히
                break
        
        # 6. MariaDB 저장 형태 예시
        print(f"\n💾 MariaDB 저장 형태 예시:")
        
        # Dense 벡터
        dense_for_db = embeddings[0].tolist()
        print(f"  Dense 벡터 길이: {len(dense_for_db)}")
        print(f"  Dense 벡터 차원: {len(dense_for_db)}")
        
        # Sparse 키워드 (Kiwi)
        first_text_result = kiwi.analyze(test_texts[0])
        first_text_nouns = [token.form for token in first_text_result[0][0] if token.tag.startswith('N')]
        
        sparse_for_db = {
            "keywords": ", ".join(first_text_nouns),
            "weights": {noun: 1.0 for noun in first_text_nouns},
            "extraction_method": "kiwi",
            "total_tokens": len(first_text_result[0][0])
        }
        print(f"  Sparse JSON 예시:")
        print(f"  {json.dumps(sparse_for_db, indent=2, ensure_ascii=False)}")
        
        # 7. 유사도 테스트
        vec1 = embeddings[0]
        vec2 = embeddings[1]
        cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        print(f"\n🎯 유사도 테스트:")
        print(f"  '러닝' vs '영어면접' 유사도: {cosine_sim:.4f}")
        
        print("\n" + "=" * 50)
        print("🎉 GGUF + Kiwi 조합 테스트 완료!")
        print("✅ Dense 벡터 생성 성공 (GGUF)")
        print("✅ Sparse 키워드 추출 성공 (Kiwi)")
        print("✅ MariaDB 저장 형태 변환 확인")
        print(f"📊 총 시스템 크기: ~460MB (GGUF 438MB + Kiwi ~20MB)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gguf_kiwi()
    if not success:
        exit(1)
