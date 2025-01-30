from core.config import get_connection_pool


def fetch_gaji_komponen(profil_gaji_id: int = None) -> list:
    query = """
    SELECT
        id,
        profil_gaji_id,
        urut,
        kode,
        nama,
        nilai,
        formula,
        jenis_gaji,
        is_reference
    FROM
        gaji_komponen
    WHERE
        is_deleted = %s
    """
    params = (False,)
    if profil_gaji_id:
        query += " AND profil_gaji_id = %s"
        params = (False, profil_gaji_id)

    query += " ORDER BY urut ASC"

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
