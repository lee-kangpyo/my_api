# gunicorn.conf.py
from datetime import datetime
import os
import logging.handlers

if not os.path.exists("/app/log"):
    os.makedirs("/app/log")
    #os.makedirs("/app/log/apiServer")

log_file = f"/app/log/access.log"

# Configure the logging handler to use TimedRotatingFileHandler
log_handler = logging.handlers.TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=30)  # 매일 분리하고 최대 30개 파일 보존

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_handler.setFormatter(logging.Formatter(log_format))

log = logging.getLogger("gunicorn.error")
log.addHandler(log_handler)
log.setLevel(logging.INFO)

# SmallStep 분석 로그 설정
smallstep_log_file = "/app/log/smallstep_analytics.log"
smallstep_handler = logging.handlers.TimedRotatingFileHandler(
    smallstep_log_file, when="midnight", interval=1, backupCount=30
)
smallstep_handler.setFormatter(logging.Formatter(log_format))

smallstep_analytics_log = logging.getLogger("smallstep.analytics")
smallstep_analytics_log.addHandler(smallstep_handler)
smallstep_analytics_log.setLevel(logging.INFO)
smallstep_analytics_log.propagate = False  # 중복 로깅 방지

# 에러 전용 로그 설정 (모든 ERROR 레벨 통합)
error_log_file = "/app/log/error.log"
error_handler = logging.handlers.TimedRotatingFileHandler(
    error_log_file, when="midnight", interval=1, backupCount=30
)
error_handler.setLevel(logging.ERROR)  # ERROR 레벨만 수집
error_handler.setFormatter(logging.Formatter(log_format))

# 루트 로거에 에러 핸들러 추가 (모든 에러 캐치)
root_logger = logging.getLogger()
root_logger.addHandler(error_handler)

bind = "0.0.0.0:80"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
reload = True
loglevel = "info"
forwarded_allow_ips = "*"



# from datetime import datetime
# import os

# if not os.path.exists("log"):
#     os.makedirs("log")
#     os.makedirs("log/gunicorn")

# bind = "0.0.0.0:80"
# workers = 2
# worker_class = "uvicorn.workers.UvicornWorker"
# reload = True
# accesslog = f"./log/gunicorn/access_{datetime.now().strftime('%Y-%m-%d_%H')}.log"
# errorlog = f"./log/gunicorn/error_{datetime.now().strftime('%Y-%m-%d_%H')}.log"
# loglevel = "info"