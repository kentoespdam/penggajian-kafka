from core.config import get_connection_pool


def fetch_gaji_pendaptan_non_pajak_by_kode_pajak(kode_pajak: str):
    query = "SELECT nominal FROM gaji_pendapatan_non_pajak WHERE kode = %s"
    params = (kode_pajak,)

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()