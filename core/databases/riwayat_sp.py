from core.config import get_connection_pool


def fetch_all_riwayat_sp_by_date(start_date: str, end_date: str):
    """Fetch all riwayat SP records between a given date range."""
    query = """
            SELECT rsp.jenis_sp_id,
                   ssp.pot_tkk AS nilai
            FROM riwayat_sp AS rsp
                     INNER JOIN sanksi_sp AS ssp ON rsp.sanksi_id = ssp.id
            WHERE rsp.tanggal_mulai BETWEEN %s AND %s
            ORDER BY rsp.tanggal_mulai DESC
            """

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()


def fetch_riwayat_sp(pegawai_id: int, from_date: str, to_date: str):
    sql = """
          SELECT rsp.jenis_sp_id,
                 ssp.pot_tkk AS nilai
          FROM riwayat_sp AS rsp
                   INNER JOIN sanksi_sp AS ssp ON rsp.sanksi_id = ssp.id
          WHERE rsp.tanggal_mulai BETWEEN %s AND %s
            AND rsp.pegawai_id = %s
          ORDER BY rsp.tanggal_mulai DESC
          """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (from_date, to_date, pegawai_id))
            return cursor.fetchall()
