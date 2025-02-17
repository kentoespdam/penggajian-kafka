import pandas as pd
from core.config import get_connection_pool


def fetch_all_rumah_dinas() -> list:
    sql = "SELECT id, nama, nilai FROM rumah_dinas WHERE is_deleted = FALSE"
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


def filter_rumah_dinas_by_id(rumah_dinas_data: pd.DataFrame, rumah_dinas_id: float):
    return rumah_dinas_data[rumah_dinas_data['id'] == rumah_dinas_id].reset_index(drop=True)


def fetch_rumah_dinas_by_id(rumah_dinas_id: int) -> float:
    sql = "SELECT nilai FROM rumah_dinas WHERE id = %s AND is_deleted = FALSE"
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (int(rumah_dinas_id),))
            result = cursor.fetchone()
            return result
