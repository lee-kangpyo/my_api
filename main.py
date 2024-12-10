# uvicorn main:app --reload
# uvicorn main:app --reload --host=0.0.0.0 --port=8000
import logging
from fastapi.logger import logger as fastapi_logger

from dotenv import load_dotenv
import os
from typing import Union
from fastapi import FastAPI

from router.lotto import lotto

load_dotenv()
mode = os.getenv("MODE")

app = FastAPI(docs_url="/api/docs", redoc_url=None)

if mode == "PROD":
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger = logging.getLogger("gunicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = gunicorn_error_logger.handlers
    fastapi_logger.handlers = gunicorn_error_logger.handlers
if mode == "PROD":
    fastapi_logger.setLevel(gunicorn_logger.level)
elif mode == "DEV":
    fastapi_logger.setLevel(logging.DEBUG)

@app.get("/version", description="버전.", tags=["버전"])
async def root():
    return [
        {"version": "1.0.0.0", "detail":"fastApi 시작"},
    ]


app.include_router(lotto.router)