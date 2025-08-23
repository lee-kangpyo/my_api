#!/usr/bin/env python3
"""
경량 임베딩 모델 다운로드 및 테스트 스크립트
"""

import os
import json
import numpy as np
from llama_cpp import Llama
from huggingface_hub import model_info, hf_hub_download
from konlpy.tag import Okt

def test_lightweight_model():
    """경량 임베딩 모델 로드 및 기본 테스트"""
    
    print("🚀 경량 임베딩 모델 테스트 시작")
    print("=" * 50)
    
    try:
        # GGUF 모델 정보 확인 (puppyM 모델 사용)
        model_repo = 'puppyM/bge-m3-Q4_K_M-GGUF'
        model_filename = 'bge-m3-q4_k_m.gguf'  # 소문자!
        
        print("📊 GGUF 모델 정보 확인 중...")
        try:
            info = model_info(model_repo)
            print(f"💾 예상 모델 크기: ~600MB (Q4_K_M 양자화)")
        except Exception as e:
            print(f"⚠️ 모델 정보 확인 실패: {e}")
        
        # GGUF 모델 다운로드
        print("📥 GGUF 모델 다운로드 중... (최초 실행 시)")
        try:
            model_path = hf_hub_download(
                repo_id=model_repo,
                filename=model_filename,
                cache_dir="./models"
            )
            print(f"✅ 모델 다운로드 완료: {model_path}")
        except Exception as e:
            print(f"❌ 모델 다운로드 실패: {e}")
            return False
        
        # llama-cpp로 모델 로드
        print("🔧 GGUF 모델 로드 중...")
        model = Llama(
            model_path=model_path,
            embedding=True,  # 임베딩 모드
            verbose=False,
            n_ctx=512,  # 컨텍스트 길이
            n_threads=4  # CPU 스레드 수
        )
        print("✅ 모델 로드 완료!")
        print(f"📊 모델 정보: BGE-M3 Q4_K_M 양자화 (768차원 예상)")
        
        # 테스트 텍스트
        test_texts = [
            "3개월 내에 5km 러닝을 30분 내에 완주하기",
            "한 달 안에 영어 면접 완벽 대비하기",
            "파이썬 프로그래밍 기초부터 고급까지 마스터하기",
            "토익 900점 달성을 위한 체계적 학습 계획"
        ]
        
        print(f"\n📝 테스트 텍스트 ({len(test_texts)}개):")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. {text}")
        
        # GGUF 모델로 임베딩 생성
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
        print(f"  Dense 벡터 타입: {type(embeddings)}")
        print(f"  벡터 차원: {embeddings.shape[1]}")
        
        # Dense 벡터 예시 출력
        print(f"\n🔍 Dense 벡터 예시 (첫 번째 텍스트, 처음 10개 값):")
        dense_sample = embeddings[0][:10]
        print(f"  {dense_sample}")
        
        # KoNLPy로 실제 키워드 추출
        print(f"\n🔍 KoNLPy 키워드 추출 테스트:")
        okt = Okt()
        
        for i, text in enumerate(test_texts):
            # 명사 추출
            nouns = okt.nouns(text)
            # 형태소 분석 (품사 태깅)
            morphs = okt.pos(text)
            
            print(f"\n  텍스트 {i+1}: {text}")
            print(f"  명사: {nouns}")
            print(f"  주요 형태소: {[word for word, pos in morphs if pos in ['Noun', 'Verb', 'Adjective']][:5]}")
            
            if i == 0:  # 첫 번째만 자세히
                break
        
        # 유사도 테스트
        print(f"\n🎯 유사도 테스트:")
        
        # 첫 번째와 두 번째 텍스트 간 코사인 유사도
        vec1 = embeddings[0]
        vec2 = embeddings[1]
        
        cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        print(f"  '러닝' vs '영어면접' 유사도: {cosine_sim:.4f}")
        
        vec3 = embeddings[2]
        cosine_sim2 = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
        print(f"  '러닝' vs '파이썬' 유사도: {cosine_sim2:.4f}")
        
        # MariaDB 저장 형태 예시
        print(f"\n💾 MariaDB 저장 형태 예시:")
        
        # Dense 벡터를 리스트로 변환 (MariaDB VECTOR 타입용)
        dense_for_db = embeddings[0].tolist()
        print(f"  Dense 벡터 길이: {len(dense_for_db)}")
        print(f"  Dense 벡터 타입: {type(dense_for_db)}")
        
        # KoNLPy 결과를 MariaDB JSON 형태로 변환
        okt_analyzer = Okt()  # 새로 생성
        first_text_nouns = okt_analyzer.nouns(test_texts[0])
        sparse_for_db = {
            "keywords": ", ".join(first_text_nouns),
            "weights": {noun: 1.0 for noun in first_text_nouns},  # 단순 가중치
            "extraction_method": "konlpy_okt",
            "pos_tags": dict(okt_analyzer.pos(test_texts[0])[:5])  # 상위 5개 품사
        }
        print(f"  Sparse JSON 예시: {json.dumps(sparse_for_db, indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 50)
        print("🎉 한국어 특화 BGE-M3 모델 테스트 완료!")
        print("✅ 모델이 정상적으로 작동합니다.")
        print("✅ Dense 임베딩 생성 확인")
        print("✅ 키워드 추출 시뮬레이션 확인")
        print("✅ MariaDB 저장 형태 변환 확인")
        print(f"📊 모델: ONNX 최적화 + 한국어 특화")
        print(f"🔧 DB 스키마 수정 필요: VECTOR({embeddings.shape[1]}) 차원")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        print("🔍 다음을 확인하세요:")
        print("   1. 필요한 패키지가 모두 설치되었는지")
        print("   2. 인터넷 연결이 정상인지 (모델 다운로드용)")
        print("   3. 충분한 디스크 공간이 있는지")
        return False

if __name__ == "__main__":
    success = test_lightweight_model()
    if not success:
        exit(1)
