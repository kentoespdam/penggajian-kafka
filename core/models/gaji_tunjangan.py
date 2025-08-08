import pandas as pd

from core.config import get_connection_pool


def fetch_tunjangan():
    query = """SELECT id,
                      jenis_tunjangan,
                      IFNULL(level_id, 0)    AS level_id,
                      IFNULL(golongan_id, 0) AS golongan_id,
                      nominal
               FROM gaji_tunjangan
               WHERE is_deleted = %s"""
    params = (False,)

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return pd.DataFrame(cursor.fetchall())
