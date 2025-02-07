from core.config import get_connection_pool


def fetch_organisasi_by_level(level: int | list[int]) -> list[tuple]:
    """
    Fetch all organisasi records that match the given level.

    Args:
        level: The level of the organisasi to fetch.

    Returns:
        A list of tuples containing the id, parent_id, level_org, kode, and nama of the organisasi.
    """
    query = """
        SELECT id, parent_id, level_org, kode, nama
        FROM organisasi
        WHERE is_deleted = FALSE
    """
    params = ()
    if isinstance(level, int):
        query += " AND level_org = %s"
        params = (level,)
    else:
        query += " AND level_org IN %s"
        params = (tuple(level),)

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
