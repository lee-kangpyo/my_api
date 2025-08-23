#!/usr/bin/env python3
"""
KoNLPy 제외한 간단한 테스트
"""

print("🚀 KoNLPy 제외 테스트 시작")
print("=" * 30)

try:
    print("1. 기본 패키지 테스트...")
    import numpy as np
    print("   ✅ numpy 로드 성공")
    
    import json
    print("   ✅ json 로드 성공")
    
    print("2. llama-cpp 테스트...")
    from llama_cpp import Llama
    print("   ✅ llama-cpp 임포트 성공")
    
    print("3. huggingface-hub 테스트...")
    from huggingface_hub import model_info
    print("   ✅ huggingface-hub 임포트 성공")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("=" * 30)
print("🎉 KoNLPy 제외 테스트 완료")
