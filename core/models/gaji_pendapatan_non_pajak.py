import pandas as pd

from core.config import get_connection_pool


def fetch_gaji_pendapatan_non_pajak():
    query = "SELECT id, kode, nominal FROM gaji_pendapatan_non_pajak"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return pd.DataFrame(cursor.fetchall())
