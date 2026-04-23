import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

SSL_CA_PATH = 'D:/smallStep/backend/ssl/ca-cert.pem'
ssl_config = {'ca': SSL_CA_PATH, 'check_hostname': False, 'verify_mode': False}

url = os.getenv('smallstep_mysql')
engine = create_engine(url, pool_pre_ping=True, connect_args={'ssl': ssl_config})

with engine.connect() as conn:
    result = conn.execute(text("SHOW GRANTS FOR 'stepUser'@'%'"))
    for row in result:
        print(row)
