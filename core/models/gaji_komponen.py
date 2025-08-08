import pandas as pd

from core.config import get_connection_pool


def fetch_gaji_komponen():
    query = """SELECT id,
                      profil_gaji_id,
                      urut,
                      kode,
                      nama,
                      nilai,
                      formula,
                      jenis_gaji,
                      is_reference
               FROM gaji_komponen
               WHERE is_deleted = %s"""
    params = (False,)

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return pd.DataFrame(cursor.fetchall())
