import pandas as pd

from core.config import get_connection_pool


def fetch_rumah_dinas():
    query = "SELECT id, nama, nilai FROM rumah_dinas WHERE is_deleted = %s"
    params = (False,)
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return pd.DataFrame(cursor.fetchall())