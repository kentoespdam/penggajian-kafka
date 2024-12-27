import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVER = f"{os.getenv('KAFKA_SERVER')}"
KAFKA_GROUP_ID = f"{os.getenv('KAFKA_GROUP_ID')}"
PENGGAJIAN_TOPIC = f"{os.getenv('PENGGAJIAN_TOPIC')}"
DB_URL=f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8"
ENGINE=create_engine(
    str(DB_URL),
    echo=True
)