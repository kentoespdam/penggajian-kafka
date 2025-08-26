import logging
import os

from dotenv import load_dotenv
from pymysql.cursors import DictCursor
from pymysqlpool import Connection, ConnectionPool

load_dotenv()
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'),
                    format='%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)', encoding='utf-8')
logging.getLogger("aiokafka").setLevel("ERROR")
LOGGER = logging.getLogger(__name__)

KAFKA_SERVER = os.getenv('KAFKA_SERVER')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC')
HITUNG_ULANG_TOPIC = os.getenv('HITUNG_ULANG_TOPIC')

KODE_CABANG_PWT1 = str(os.getenv('KODE_CABANG_PWT1'))
KODE_CABANG_PWT2 = str(os.getenv('KODE_CABANG_PWT2'))
KODE_CABANG_AJB = str(os.getenv('KODE_CABANG_AJB'))
KODE_CABANG_WGN = str(os.getenv('KODE_CABANG_WGN'))
KODE_CABANG_BMS = str(os.getenv('KODE_CABANG_BMS'))


def get_connection_pool(autocommit: bool = False) -> Connection:
    config = {
        "size": 10,
        "maxsize": 15,
        "pre_create_num": 2,
        "name": "kepegawaian-pool",
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,
        'autocommit': autocommit
    }

    return ConnectionPool(**config).get_connection()
