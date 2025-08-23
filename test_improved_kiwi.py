#!/usr/bin/env python3
"""
개선된 Kiwi 키워드 추출 테스트
"""

import re
import json
import numpy as np
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from kiwipiepy import Kiwi

def extract_improved_keywords(text, kiwi):
    """개선된 키워드 추출 함수"""
    
    # 1. 숫자+단위 패턴 먼저 추출
    number_unit_patterns = [
        r'\d+개월',  # 3개월
        r'\d+km',    # 5km  
        r'\d+분',    # 30분
        r'\d+시간',  # 2시간
        r'\d+일',    # 7일
        r'\d+주',    # 4주
        r'\d+년',    # 1년
        r'\d+점',    # 900점
        r'\d+회',    # 10회
        r'\d+번',    # 5번
    ]
    
    number_units = []
    for pattern in number_unit_patterns:
        matches = re.findall(pattern, text)
        number_units.extend(matches)
    
    # 2. Kiwi로 명사 추출
    result = kiwi.analyze(text)
    nouns = [token.form for token in result[0][0] if token.tag.startswith('N') and len(token.form) > 1]
    
    # 3. 동사, 형용사도 추출 (의미있는 것들)
    verbs_adjs = [token.form for token in result[0][0] 
                  if (token.tag.startswith('V') or token.tag.startswith('A')) 
                  and len(token.form) > 1]
    
    # 4. 불용어 제거
    stop_words = {'내에', '안에', '까지', '부터', '에서', '으로', '를', '을', '이', '가', '의', '에', '와', '과'}
    
    # 5. 최종 키워드 조합
    all_keywords = []
    all_keywords.extend(number_units)  # 숫자+단위 우선
    all_keywords.extend([noun for noun in nouns if noun not in stop_words])
    all_keywords.extend([word for word in verbs_adjs if word not in stop_words][:3])  # 주요 동사/형용사 3개만
    
    # 6. 중복 제거하면서 순서 유지
    unique_keywords = []
    for keyword in all_keywords:
        if keyword not in unique_keywords:
            unique_keywords.append(keyword)
    
    return unique_keywords

def test_improved_kiwi():
    """개선된 Kiwi 키워드 추출 테스트"""
    
    print("🚀 개선된 Kiwi 키워드 추출 테스트")
    print("=" * 50)
    
    try:
        # Kiwi 로드
        print("🥝 Kiwi 로드 중...")
        kiwi = Kiwi()
        print("✅ Kiwi 로드 완료!")
        
        # 테스트 텍스트들
        test_texts = [
            "3개월 내에 5km 러닝을 30분 내에 완주하기",
            "한 달 안에 영어 면접 완벽 대비하기", 
            "파이썬 프로그래밍 기초부터 고급까지 마스터하기",
            "토익 900점 달성을 위한 체계적 학습 계획",
            "주 3회 헬스장에서 근력 운동하기",
            "매일 1시간씩 독서 습관 만들기"
        ]
        
        print(f"\n📝 테스트 텍스트 ({len(test_texts)}개):")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. {text}")
        
        print(f"\n🔍 개선된 키워드 추출 결과:")
        
        for i, text in enumerate(test_texts):
            print(f"\n  텍스트 {i+1}: {text}")
            
            # 기존 방식
            result = kiwi.analyze(text)
            old_nouns = [token.form for token in result[0][0] if token.tag.startswith('N')]
            print(f"  기존 명사: {old_nouns}")
            
            # 개선된 방식
            improved_keywords = extract_improved_keywords(text, kiwi)
            print(f"  개선된 키워드: {improved_keywords}")
            
            # 가중치 부여 (숫자+단위는 높은 가중치)
            weights = {}
            for keyword in improved_keywords:
                if re.match(r'\d+\w+', keyword):  # 숫자+단위
                    weights[keyword] = 2.0
                elif len(keyword) > 2:  # 긴 단어
                    weights[keyword] = 1.5
                else:
                    weights[keyword] = 1.0
            
            print(f"  가중치: {weights}")
            
            if i >= 2:  # 처음 3개만 자세히
                break
        
        # MariaDB 저장 형태 예시
        print(f"\n💾 개선된 MariaDB 저장 형태:")
        first_keywords = extract_improved_keywords(test_texts[0], kiwi)
        
        sparse_data = {
            "keywords": ", ".join(first_keywords),
            "weights": {kw: (2.0 if re.match(r'\d+\w+', kw) else 1.5 if len(kw) > 2 else 1.0) 
                       for kw in first_keywords},
            "extraction_method": "kiwi_improved",
            "patterns_used": ["number_unit", "nouns", "verbs_adjs"],
            "total_keywords": len(first_keywords)
        }
        
        print(f"  {json.dumps(sparse_data, indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 50)
        print("🎉 개선된 키워드 추출 테스트 완료!")
        print("✅ 숫자+단위 패턴 추출 (3개월, 5km, 30분)")
        print("✅ 의미있는 명사/동사/형용사 추출")
        print("✅ 불용어 제거 및 가중치 부여")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_improved_kiwi()
