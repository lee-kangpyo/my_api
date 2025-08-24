#!/usr/bin/env python3
"""
토큰 디버깅 스크립트
"""

from kiwipiepy import Kiwi

def debug_tokens():
    kiwi = Kiwi()
    
    text = "12월까지 토익스피킹 3시스템 레벨7 달성하기"
    print(f"원본: {text}")
    print("-" * 50)
    
    tokens = kiwi.tokenize(text)
    
    print(f"총 토큰 수: {len(tokens)}")
    
    for i, token in enumerate(tokens):
        end_pos = token.start + len(token.form)
        print(f"{i:2d}: '{token.form}' (tag:{token.tag}) pos:{token.start}-{end_pos}")
        
        # 레벨7 주변 확인
        if token.form in ["레벨", "7"] or "레벨" in token.form or "7" in token.form:
            print(f"    *** 관심 토큰: {token.form} ***")
            
        # 인접 토큰과의 거리 확인
        if i + 1 < len(tokens):
            next_token = tokens[i + 1]
            gap = next_token.start - end_pos
            if gap == 0:
                print(f"    → 다음 토큰 '{next_token.form}'과 붙어있음!")
            elif gap > 0:
                print(f"    → 다음 토큰 '{next_token.form}'과 {gap}칸 떨어짐")

if __name__ == "__main__":
    debug_tokens()
