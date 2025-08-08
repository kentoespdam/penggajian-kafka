import pandas as pd

from core.config import get_connection_pool


def fetch_gaji_potongan_tkk():
    sql = """
          SELECT id, status_pegawai, IFNULL(level_id, 0) AS level_id, IFNULL(golongan_id, 0) AS golongan_id, nominal
          FROM gaji_potongan_tkk
          WHERE is_deleted = %s
          """
    parameters = (False,)

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            return pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
