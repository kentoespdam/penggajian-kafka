from core.config import get_connection_pool


def fetch_rumah_dinas_by_id(rumah_dinas_id: int) -> float:
    sql = "SELECT nilai FROM rumah_dinas WHERE id = %s AND is_deleted = FALSE"
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (rumah_dinas_id,))
            result = cursor.fetchone()
            return result["nilai"] if result else 0.0
