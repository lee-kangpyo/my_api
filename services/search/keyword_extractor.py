#!/usr/bin/env python3
"""
키워드 추출 서비스
다양한 키워드 추출 방식을 지원하는 모듈
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from kiwipiepy import Kiwi

# 로깅 설정
logger = logging.getLogger(__name__)

class KeywordExtractor(ABC):
    """키워드 추출 인터페이스"""
    
    @abstractmethod
    def extract_keywords(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 키워드를 추출합니다.
        
        Args:
            text (str): 키워드를 추출할 텍스트
            
        Returns:
            Dict[str, Any]: 키워드 정보
        """
        pass

class BasicKiwiExtractor(KeywordExtractor):
    """기본 Kiwi 형태소 분석 키워드 추출"""
    
    def __init__(self):
        """기본 Kiwi 추출기 초기화"""
        self.kiwi = None
        self.method_name = "basic_kiwi"
        logger.info("BasicKiwiExtractor 초기화 완료")
    
    def _get_kiwi(self):
        """Kiwi 분석기 lazy loading"""
        if self.kiwi is None:
            logger.info("Kiwi 형태소 분석기 로딩 중...")
            self.kiwi = Kiwi()
            logger.info("✅ Kiwi 분석기 로딩 완료!")
        return self.kiwi
    
    def extract_keywords(self, text: str) -> Dict[str, Any]:
        """기본 명사 추출"""
        try:
            kiwi = self._get_kiwi()
            
            # 형태소 분석 및 명사 추출
            analyzed = kiwi.analyze(text)
            if not analyzed or not analyzed[0]:
                return {
                    "keywords": "",
                    "weights": {},
                    "extraction_method": self.method_name,
                    "total_tokens": 0
                }
            
            # 명사만 추출
            nouns = []
            for token in analyzed[0][0]:
                if token.tag.startswith('N') and len(token.form) > 1:  # 명사 + 1글자 이상
                    nouns.append(token.form)
            
            # 중복 제거 및 빈도 계산
            noun_counts = {}
            for noun in nouns:
                noun_counts[noun] = noun_counts.get(noun, 0) + 1
            
            # 가중치 계산 (단순 빈도 기반)
            total_count = sum(noun_counts.values())
            weights = {}
            if total_count > 0:
                for noun, count in noun_counts.items():
                    weights[noun] = count / total_count
            
            # 키워드 문자열 생성
            keywords_str = ", ".join(noun_counts.keys())
            
            return {
                "keywords": keywords_str,
                "weights": weights,
                "extraction_method": self.method_name,
                "total_tokens": len(kiwi.tokenize(text))
            }
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            raise

class ImprovedKiwiExtractor(KeywordExtractor):
    """개선된 Kiwi 키워드 추출 (숫자+단위 조합 지원)"""
    
    def __init__(self):
        """개선된 Kiwi 추출기 초기화"""
        self.kiwi = None
        self.method_name = "improved_kiwi"
        logger.info("ImprovedKiwiExtractor 초기화 완료")
    
    def _get_kiwi(self):
        """Kiwi 분석기 lazy loading"""
        if self.kiwi is None:
            logger.info("Kiwi 형태소 분석기 로딩 중...")
            self.kiwi = Kiwi()
            logger.info("✅ Kiwi 분석기 로딩 완료!")
        return self.kiwi
    
    def extract_keywords(self, text: str) -> Dict[str, Any]:
        """개선된 키워드 추출 (숫자+단위 조합)"""
        try:
            kiwi = self._get_kiwi()
            
            # 토큰화
            tokens = kiwi.tokenize(text)
            if not tokens:
                return {
                    "keywords": "",
                    "weights": {},
                    "extraction_method": self.method_name,
                    "total_tokens": 0
                }
            
            # 의미있는 키워드 추출
            meaningful_keywords = []
            i = 0
            
            while i < len(tokens):
                token = tokens[i]
                
                # 숫자 + 단위 조합 확인 (붙어있는 경우만)
                if (token.tag == 'SN' and i + 1 < len(tokens) and 
                    tokens[i + 1].tag.startswith('N')):
                    
                    next_token = tokens[i + 1]
                    # 원본 텍스트에서 두 토큰이 붙어있는지 확인
                    current_end = token.start + len(token.form)
                    next_start = next_token.start
                    
                    if current_end == next_start:  # 붙어있음
                        # "3개월" 패턴
                        combined = token.form + next_token.form
                        meaningful_keywords.append(combined)
                        i += 2  # 두 토큰을 하나로 처리
                    else:  # 띄어져 있음
                        # "7 달성" → 각각 따로 처리
                        meaningful_keywords.append(token.form)  # "7"만
                        i += 1
                        
                # 단위 + 숫자 조합 확인 (레벨7 패턴)
                elif (token.tag.startswith('N') and i + 1 < len(tokens) and 
                      tokens[i + 1].tag == 'SN'):
                    
                    next_token = tokens[i + 1]
                    # 원본 텍스트에서 두 토큰이 붙어있는지 확인
                    current_end = token.start + len(token.form)
                    next_start = next_token.start
                    
                    if current_end == next_start:  # 붙어있음
                        # "레벨7" 패턴
                        combined = token.form + next_token.form
                        meaningful_keywords.append(combined)
                        i += 2  # 두 토큰을 하나로 처리
                    else:  # 띄어져 있음
                        # "레벨 7" → 각각 따로 처리
                        meaningful_keywords.append(token.form)
                        i += 1
                    
                # 숫자 + 영문 단위 (붙어있는 경우만)
                elif (token.tag == 'SN' and i + 1 < len(tokens) and 
                      tokens[i + 1].tag == 'SL' and 
                      len(tokens[i + 1].form) <= 3):  # km, kg 등 짧은 단위
                    
                    next_token = tokens[i + 1]
                    current_end = token.start + len(token.form)
                    next_start = next_token.start
                    
                    if current_end == next_start:  # 붙어있음
                        # "5km" 등
                        combined = token.form + next_token.form
                        meaningful_keywords.append(combined)
                        i += 2
                    else:  # 띄어져 있음
                        meaningful_keywords.append(token.form)
                        i += 1
                    
                # 일반 명사
                elif token.tag.startswith('N') and len(token.form) > 1:
                    meaningful_keywords.append(token.form)
                    i += 1
                    
                else:
                    i += 1
            
            # 중복 제거 및 빈도 계산
            keyword_counts = {}
            for keyword in meaningful_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            # 가중치 계산
            total_count = sum(keyword_counts.values())
            weights = {}
            if total_count > 0:
                for keyword, count in keyword_counts.items():
                    weights[keyword] = count / total_count
            
            # 키워드 문자열 생성
            keywords_str = ", ".join(keyword_counts.keys())
            
            return {
                "keywords": keywords_str,
                "weights": weights,
                "extraction_method": self.method_name,
                "total_tokens": len(tokens)
            }
            
        except Exception as e:
            logger.error(f"개선된 키워드 추출 실패: {e}")
            raise

class KeywordExtractorFactory:
    """키워드 추출기 팩토리"""
    
    _extractors = {
        "basic_kiwi": BasicKiwiExtractor,
        "improved_kiwi": ImprovedKiwiExtractor,
    }
    
    @classmethod
    def create_extractor(cls, method: str = "basic_kiwi") -> KeywordExtractor:
        """
        키워드 추출기 생성
        
        Args:
            method (str): 추출 방식 ("basic_kiwi", "improved_kiwi")
            
        Returns:
            KeywordExtractor: 키워드 추출기 인스턴스
        """
        if method not in cls._extractors:
            available_methods = list(cls._extractors.keys())
            raise ValueError(f"지원하지 않는 추출 방식: {method}. 사용 가능: {available_methods}")
        
        extractor_class = cls._extractors[method]
        return extractor_class()
    
    @classmethod
    def get_available_methods(cls) -> List[str]:
        """사용 가능한 추출 방식 목록 반환"""
        return list(cls._extractors.keys())

# 편의를 위한 기본 추출기 인스턴스
default_extractor = KeywordExtractorFactory.create_extractor("basic_kiwi")
