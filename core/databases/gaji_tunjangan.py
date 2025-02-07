import pandas as pd
from core.config import get_connection_pool
from core.enums import TUNJANGAN


from typing import Optional

from core.config import get_connection_pool
from core.enums import TUNJANGAN


def fetch_all_tunjangan_data() -> list:
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
            is_deleted = FALSE
        """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def filter_tunjangan_data(
        list: pd.DataFrame,
    reference: int, level_id: Optional[int] = None, golongan_id: Optional[int] = None
) -> pd.DataFrame:
    level_id = level_id if reference != TUNJANGAN.BERAS.value else 7
    if level_id and level_id in [5, 6]:
        return list[(list["jenis_tunjangan"] == reference) & (list["level_id"] == level_id)].reset_index(drop=True)
    else:
        return list[(list["jenis_tunjangan"] == reference) & (list["golongan_id"] == golongan_id)].reset_index(drop=True)


def fetch_nominal_tunjangan_data(
    reference: int, level_id: Optional[int] = None, golongan_id: Optional[int] = None
) -> Optional[dict]:
    """
    Fetches a single row from gaji_tunjangan based on the given reference and optional level_id and golongan_id.

    Args:
        reference: The reference ID of the tunjangan.
        level_id: The level ID of the tunjangan if applicable.
        golongan_id: The golongan ID of the tunjangan if applicable.

    Returns:
        A tuple containing the id, jenis_tunjangan, level_id, golongan_id, and nominal of the tunjangan.
    """
    params = {"reference": reference}
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
    if level_id in [5, 6]:
        query += " AND level_id = %(level_id)s"
        params["level_id"] = int(level_id)
    elif golongan_id:
        query += " AND golongan_id = %(golongan_id)s"
        params["golongan_id"] = int(golongan_id)

    if reference == TUNJANGAN.BERAS.value:
        params["level_id"] = 7

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
