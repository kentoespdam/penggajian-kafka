from core.config import CONNECTION, ENGINE, POOL
from icecream import ic

from core.enums import STATUS_PEGAWAI


def get_potongan_tkk_data(root_batch_id: str, nipam: str):
    sql = """
        SELECT
            SUM(potongan) AS potongan 
        FROM 
            gaji_batch_potongan_tkk 
        WHERE 
            batch_id = %s 
            AND nipam = %s
        """

    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (root_batch_id, nipam))
            data = cursor.fetchone()

    return data


def get_gaji_potongan_tkk_data(status_pegawai: int, level_id: int = None, golongan_id: int = None):
    parameters = {
        "status_pegawai": status_pegawai,
    }
    sql = """
        SELECT
            nominal
        FROM
            gaji_potongan_tkk
        WHERE
            status_pegawai = %(status_pegawai)s
        """
    if level_id:
        sql += " AND level_id = %(level_id)s"
        parameters["level_id"] = level_id
    if golongan_id:
        sql += " AND golongan_id = %(golongan_id)s"
        parameters["golongan_id"] = golongan_id

    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, args=parameters)
            data = cursor.fetchone()

    return data
