import pandas as pd

from core.config import get_connection_pool


def fetch_parameter_setting():
    sql = """
          SELECT kode, nominal
          FROM gaji_parameter_setting
          WHERE is_deleted = %s
          """
    parameters = (False,)

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            return pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
