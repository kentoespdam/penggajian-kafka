from core.config import get_connection_pool

def fetch_all_riwayat_sp_by_date(from_date: str, to_date: str):
    sql = """
        SELECT
            jenis_sp,
            CASE
                WHEN jenis_sp = 0 THEN 1
                WHEN jenis_sp = 1 THEN 2
                WHEN jenis_sp = 2 THEN 3
                WHEN jenis_sp = 3 THEN -1
                WHEN jenis_sp = 4 THEN 0
            END AS nilai
        FROM 
            riwayat_sp
        WHERE
            tanggal_mulai BETWEEN %s AND %s
        ORDER BY 
            tanggal_mulai DESC
    """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (from_date, to_date))
            return cursor.fetchall()

def fetch_riwayat_sp(pegawai_id: int, from_date: str, to_date: str):
    sql = """
        SELECT
            jenis_sp,
            CASE
                WHEN jenis_sp = 0 THEN 1
                WHEN jenis_sp = 1 THEN 2
                WHEN jenis_sp = 2 THEN 3
                WHEN jenis_sp = 3 THEN -1
                WHEN jenis_sp = 4 THEN 0
            END AS nilai
        FROM riwayat_sp
        WHERE pegawai_id = %s
        AND tanggal_mulai BETWEEN %s AND %s
        ORDER BY tanggal_mulai DESC
    """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (pegawai_id, from_date, to_date))
            return cursor.fetchall()