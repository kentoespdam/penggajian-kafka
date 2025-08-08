import pandas as pd

from core.config import get_connection_pool


def fetch_organisasi_by_level(level: int | list[int]) -> pd.DataFrame:
    query = """
            SELECT id, parent_id, level_org, kode, nama, short_name
            FROM organisasi
            WHERE is_deleted = %s
            """
    params = (False,)
    if isinstance(level, int):
        query += " AND level_org = %s"
        params += (level,)
    else:
        query += " AND level_org IN %s"
        params += (tuple(level),)

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return pd.DataFrame(cursor.fetchall())
