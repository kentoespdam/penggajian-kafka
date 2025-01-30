from core.config import get_connection_pool


def fetch_gaji_profil(profil_id: str = None) -> list | dict:
    query = """
    SELECT
        id,
        kode,
        nama,
        nominal
    FROM
        gaji_profil
    """
    params = ()
    if profil_id:
        query += " WHERE id = %s"
        params = (profil_id,)

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone() if profil_id else cursor.fetchall()
