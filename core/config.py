import datetime
import os
import pymysql
from dotenv import load_dotenv
import pymysqlpool
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="logs/penggajian.log",
                    encoding="utf-8", level=logging.DEBUG)

load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_SERVER')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID')
PENGGAJIAN_TOPIC = os.getenv('PENGGAJIAN_TOPIC')


def get_connection_pool(autocommit: bool = False) -> pymysqlpool.Connection:
    """
    Return a connection from a pool of connections to the database.

    The connection pool is created with the following configuration:
    - size: 10
    - maxsize: 15
    - pre_create_num: 2
    - name: 'connection_pool'
    - autocommit: False
    - host: DB_HOST environment variable
    - port: int(DB_PORT environment variable)
    - user: DB_USER environment variable
    - password: DB_PASS environment variable
    - db: DB_NAME environment variable
    - charset: utf8mb4
    - cursorclass: pymysql.cursors.DictCursor

    Parameters:
    autocommit (bool): Whether to enable autocommit mode. Defaults to False.

    Returns:
    pymysqlpool.Connection: A connection to the database.
    """
    config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    return pymysqlpool.ConnectionPool(
        size=10,
        maxsize=15,
        pre_create_num=2,
        name='connection_pool',
        autocommit=autocommit,
        **config
    ).get_connection()


def log_info(message: str) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{now} {message}")


def log_error(message: str) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.error(f"{now} {message}")


def log_debug(message: str) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.debug(f"{now} {message}")
