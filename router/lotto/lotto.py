from fastapi import APIRouter, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from database import get_db

import json

from router.lotto.lotto_schema import Suggetion, Bug
from models import LOTTOSUGGESTION

from starlette import status
from fastapi.responses import JSONResponse
from datetime import datetime

from typing import List

import logging

logging.basicConfig(level=logging.INFO)  # 로깅 레벨 설정

router = APIRouter(
    prefix="/api/lotto",
)

import os

# 저장할 폴더 경로 설정
UPLOAD_FOLDER = "uploads"

# 폴더가 존재하지 않으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/suggestion", description="기능 제안 하기", tags=["로또앱"])
def save_suggestion(suggestion:Suggetion, db: Session = Depends(get_db)):
    try:
        suggestionInfo = LOTTOSUGGESTION(SUGGESTION = suggestion.suggestion, ADDITIONAL = suggestion.additional)
        db.add(suggestionInfo)
        db.commit()
        return JSONResponse(status_code=status.HTTP_201_CREATED, content="성공")
    except Exception as e:
        logging.error("User addition failed:", str(e))
        return JSONResponse(content="제안 저장 중 오류 발생. 잠시 후 다시 시도해주세요.", status_code=status.HTTP_400_BAD_REQUEST)
   

@router.post("/bug", description="버그 신고", tags=["로또앱"])
async def save_bug(bug:str = Form(...), step:str = Form(...), images: List[UploadFile] = File(default=[]), db: Session = Depends(get_db)):
    try:
        file_details = []
        # suggestionInfo = LOTTOSUGGESTION(SUGGESTION = suggestion.suggestion, ADDITIONAL = suggestion.additional)
        # db.add(suggestionInfo)
        # db.commit()
        # JSON 문자열을 Python dict로 변환
        
        for image in images:
            # 예시로 파일명을 출력
            print(f"Uploaded image: {image.filename}")
            print(image.size)
            file_path = os.path.join(UPLOAD_FOLDER, image.filename)
            # 파일 저장
            with open(file_path, "wb") as buffer:
                buffer.write(await image.read())
            file_details.append(image.filename)
        print(bug)
        print(step)
        print(file_details)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content="성공")
    except Exception as e:
        logging.error("User addition failed:", str(e))
        return JSONResponse(content="버그 신고 중 오류 발생. 잠시 후 다시 시도해주세요.", status_code=status.HTTP_400_BAD_REQUEST)
   
