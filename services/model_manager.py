#!/usr/bin/env python3
"""
AI 모델 로딩 및 관리 서비스
GGUF + Kiwi 모델의 싱글톤 관리
"""

import os
import logging
from typing import Optional
from threading import Lock
from llama_cpp import Llama
from kiwipiepy import Kiwi
from huggingface_hub import hf_hub_download

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """AI 모델 로딩 및 관리 클래스 (싱글톤 패턴)"""
    
    _instance = None
    _lock = Lock()
    
    # 싱글톤 생성을 위해 new 와 init을 분리함.
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._gguf_model: Optional[Llama] = None
        self._kiwi_analyzer: Optional[Kiwi] = None
        self._model_lock = Lock()
        self._kiwi_lock = Lock()
        
        # 모델 설정
        self.model_repo = 'puppyM/bge-m3-Q4_K_M-GGUF'
        self.model_filename = 'bge-m3-q4_k_m.gguf'
        self.models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        
        # Hugging Face 캐시 구조 경로
        self.hf_cache_dir = os.path.join(self.models_dir, 'models--puppyM--bge-m3-Q4_K_M-GGUF')
        
        # 모델 디렉토리 생성
        os.makedirs(self.models_dir, exist_ok=True)
        
        self._initialized = True
        logger.info("ModelManager 초기화 완료")
    
    def get_gguf_model(self) -> Llama:
        """GGUF 모델 로딩 (싱글톤)"""
        if self._gguf_model is None:
            with self._model_lock:
                if self._gguf_model is None:
                    logger.info("GGUF 모델 로딩 시작...")
                    
                    # backend/models/ 폴더를 이용한 모델 로딩 (기존 모델 재사용)
                    try:
                        logger.info(f"모델 로딩 시작: {self.model_repo}")
                        model_path = hf_hub_download(
                            repo_id=self.model_repo,
                            filename=self.model_filename,
                            local_dir=self.models_dir
                            # local_dir_use_symlinks 제거 (deprecated)
                        )
                        logger.info(f"✅ 모델 준비 완료: {model_path}")
                    except Exception as e:
                        logger.error(f"모델 준비 실패: {e}")
                        raise
                    
                    # GGUF 모델 로딩
                    try:
                        self._gguf_model = Llama(
                            model_path=model_path,
                            embedding=True,  # 임베딩 모드
                            verbose=False,
                            n_ctx=512,       # 컨텍스트 길이
                            n_threads=4      # CPU 스레드 수
                        )
                        logger.info("✅ GGUF 모델 로딩 완료!")
                        logger.info(f"📊 모델 정보: BGE-M3 Q4_K_M 양자화 (1024차원)")
                        
                    except Exception as e:
                        logger.error(f"GGUF 모델 로딩 실패: {e}")
                        raise
        
        return self._gguf_model
    
    def get_kiwi_analyzer(self) -> Kiwi:
        """Kiwi 형태소 분석기 로딩 (싱글톤)"""
        if self._kiwi_analyzer is None:
            with self._kiwi_lock:
                if self._kiwi_analyzer is None:
                    logger.info("Kiwi 형태소 분석기 로딩 시작...")
                    try:
                        self._kiwi_analyzer = Kiwi()
                        logger.info("✅ Kiwi 분석기 로딩 완료!")
                    except Exception as e:
                        logger.error(f"Kiwi 분석기 로딩 실패: {e}")
                        raise
        
        return self._kiwi_analyzer
    
    def get_model_info(self) -> dict:
        """모델 정보 반환"""
        return {
            "gguf_model": {
                "repo": self.model_repo,
                "filename": self.model_filename,
                "dimension": 1024,
                "loaded": self._gguf_model is not None
            },
            "kiwi_analyzer": {
                "loaded": self._kiwi_analyzer is not None
            },
            "models_dir": self.models_dir
        }
    
    def cleanup(self):
        """모델 정리 (메모리 해제)"""
        logger.info("모델 정리 시작...")
        
        if self._gguf_model is not None:
            # llama-cpp-python은 자동으로 정리됨
            self._gguf_model = None
            logger.info("GGUF 모델 정리 완료")
        
        if self._kiwi_analyzer is not None:
            self._kiwi_analyzer = None
            logger.info("Kiwi 분석기 정리 완료")

# 전역 모델 매니저 인스턴스
model_manager = ModelManager()
