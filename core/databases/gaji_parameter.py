from core.config import get_connection_pool


def fetch_parameter_setting_data(kode: str = None):
    query = """
        SELECT
            kode,
            nominal
        FROM
            gaji_parameter_setting
        WHERE is_deleted = FALSE
        """
    params = ()
    if kode:
        query += " AND kode = %s"
        params = (kode,)
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone() if kode else cursor.fetchall()
