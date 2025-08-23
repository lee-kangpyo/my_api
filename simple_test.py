#!/usr/bin/env python3
"""
간단한 테스트 스크립트
"""

print("🚀 간단한 테스트 시작")
print("=" * 30)

try:
    print("1. 기본 패키지 테스트...")
    import numpy as np
    print("   ✅ numpy 로드 성공")
    
    import json
    print("   ✅ json 로드 성공")
    
    print("2. KoNLPy 테스트...")
    from konlpy.tag import Okt
    print("   ✅ KoNLPy 임포트 성공")
    
    okt = Okt()
    result = okt.nouns("테스트 문장입니다")
    print(f"   ✅ KoNLPy 작동 성공: {result}")
    
    print("3. llama-cpp 테스트...")
    from llama_cpp import Llama
    print("   ✅ llama-cpp 임포트 성공")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("=" * 30)
print("🎉 테스트 완료")
