import pandas as pd

from core.config import get_connection_pool


def fetch_gaji_batch_potongan_tkk(batch_root_id: str) -> pd.DataFrame:
    query = """
            SELECT nipam, sum(potongan) AS potongan
            FROM gaji_batch_potongan_tkk
            WHERE batch_id = %s
            GROUP BY nipam"""
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (batch_root_id,))
            return pd.DataFrame(cursor.fetchall())
