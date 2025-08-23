#!/usr/bin/env python3
"""
GGUF 모델만 테스트 (KoNLPy 제외)
"""

import os
import json
import numpy as np
from llama_cpp import Llama
from huggingface_hub import model_info, hf_hub_download

def test_gguf_model():
    """GGUF 모델 테스트"""
    
    print("🚀 GGUF 모델 테스트 시작")
    print("=" * 50)
    
    try:
        # GGUF 모델 정보 확인
        model_repo = 'puppyM/bge-m3-Q4_K_M-GGUF'
        model_filename = 'bge-m3-q4_k_m.gguf'
        
        print("📊 GGUF 모델 정보 확인 중...")
        print(f"💾 예상 모델 크기: ~438MB (Q4_K_M 양자화)")
        
        # GGUF 모델 다운로드
        print("📥 GGUF 모델 다운로드 중...")
        model_path = hf_hub_download(
            repo_id=model_repo,
            filename=model_filename,
            cache_dir="./models"
        )
        print(f"✅ 모델 다운로드 완료: {model_path}")
        
        # llama-cpp로 모델 로드
        print("🔧 GGUF 모델 로드 중...")
        model = Llama(
            model_path=model_path,
            embedding=True,
            verbose=False,
            n_ctx=512,
            n_threads=4
        )
        print("✅ 모델 로드 완료!")
        
        # 테스트 텍스트
        test_texts = [
            "3개월 내에 5km 러닝을 30분 내에 완주하기",
            "한 달 안에 영어 면접 완벽 대비하기"
        ]
        
        print(f"\n📝 테스트 텍스트 ({len(test_texts)}개):")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. {text}")
        
        # 임베딩 생성
        print(f"\n🔄 임베딩 생성 중...")
        embeddings = []
        for i, text in enumerate(test_texts):
            print(f"  처리 중: {i+1}/{len(test_texts)}")
            embedding = model.create_embedding(text)
            embeddings.append(embedding['data'][0]['embedding'])
        
        embeddings = np.array(embeddings)
        
        # 결과 분석
        print(f"\n📊 임베딩 결과:")
        print(f"  Dense 벡터 shape: {embeddings.shape}")
        print(f"  벡터 차원: {embeddings.shape[1]}")
        
        # 유사도 테스트
        vec1 = embeddings[0]
        vec2 = embeddings[1]
        cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        print(f"\n🎯 유사도 테스트:")
        print(f"  '러닝' vs '영어면접' 유사도: {cosine_sim:.4f}")
        
        print("\n" + "=" * 50)
        print("🎉 GGUF 모델 테스트 완료!")
        print("✅ Dense 벡터 생성 성공")
        print(f"✅ 벡터 차원: {embeddings.shape[1]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gguf_model()
    if not success:
        exit(1)
