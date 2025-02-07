import pandas as pd
from core.config import get_connection_pool


def fetch_all_gaji_pendapatan_non_pajak():
    query = "SELECT id, kode, nominal FROM gaji_pendapatan_non_pajak"

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
        
def filter_gaji_pendapatan_non_pajak(data:pd.DataFrame, kode_pajak: str):
    return data[data['kode'] == kode_pajak].reset_index(drop=True)


def fetch_gaji_pendaptan_non_pajak_by_kode_pajak(kode_pajak: str):
    query = "SELECT nominal FROM gaji_pendapatan_non_pajak WHERE kode = %s"

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (kode_pajak,))
            return cursor.fetchone()
