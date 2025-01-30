from core.config import get_connection_pool
from core.enums import TUNJANGAN


def fetch_tunjangan_data(reference: int, level_id: int = None, golongan_id: int = None):
    params = {"reference": reference,
              "level_id": level_id, "golongan_id": golongan_id}
    query = """
        SELECT
            id,
            jenis_tunjangan,
            level_id,
            golongan_id,
            nominal
        FROM
            gaji_tunjangan
        WHERE
            jenis_tunjangan = %(reference)s
        """
    if level_id in [5, 6] and reference == TUNJANGAN.BERAS.value:
        query += " AND level_id = %(level_id)s"
    elif golongan_id:
        query += " AND golongan_id = %(golongan_id)s"

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            # print(cursor.mogrify(query, params))
            return cursor.fetchone() if level_id or golongan_id else cursor.fetchall()
