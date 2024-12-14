# gunicorn.conf.py
from datetime import datetime
import os
import logging.handlers

if not os.path.exists("/app/log"):
    os.makedirs("/app/log")
    os.makedirs("/app/log/apiServer")

log_file = f"/app/log/apiServer/access.log"

# Configure the logging handler to use TimedRotatingFileHandler
log_handler = logging.handlers.TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=30)  # 매일 분리하고 최대 30개 파일 보존

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_handler.setFormatter(logging.Formatter(log_format))

log = logging.getLogger("gunicorn.error")
log.addHandler(log_handler)
log.setLevel(logging.INFO)

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