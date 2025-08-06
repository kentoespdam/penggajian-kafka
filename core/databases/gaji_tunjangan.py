from typing import Optional

import pandas as pd

from core.config import get_connection_pool
from core.enums import TUNJANGAN


def fetch_all_tunjangan_data():
    query = """
            SELECT id,
                   jenis_tunjangan,
                   level_id,
                   golongan_id,
                   nominal
            FROM gaji_tunjangan
            WHERE is_deleted = FALSE \
            """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def filter_tunjangan_data(
        tunjangan_list: pd.DataFrame,
        reference: int,
        level_id: Optional[int] = None,
        golongan_id: Optional[int] = None
) -> pd.DataFrame:
    """
    Filters a list of tunjangans to a single row based on the given tunjangan ID, level ID, and golongan ID.

    Args:
        tunjangan_list: The list of tunjangans.
        reference: The ID of the tunjangan to filter.
        level_id: The level ID of the tunjangan if applicable.
        golongan_id: The golongan ID of the tunjangan if applicable.

    Returns:
        A DataFrame containing a single row of the filtered tunjangan.
    """
    level_id = level_id if reference != TUNJANGAN.BERAS.value else 7
    if level_id is not None and level_id in [5, 6]:
        return tunjangan_list[
            (tunjangan_list["jenis_tunjangan"] == reference) &
            (tunjangan_list["level_id"] == level_id)
            ].reset_index(drop=True)
    else:
        return tunjangan_list[
            (tunjangan_list["jenis_tunjangan"] == reference) &
            (tunjangan_list["golongan_id"] == golongan_id)
            ].reset_index(drop=True)


def fetch_nominal_tunjangan(
        tunjangan_id: int, level_id: Optional[int] = None, golongan_id: Optional[int] = None
) -> Optional[dict]:
    """
    Fetches a single row from gaji_tunjangan based on the given tunjangan_id and optional level_id and golongan_id.

    Args:
        tunjangan_id: The ID of the tunjangan.
        level_id: The level ID of the tunjangan if applicable.
        golongan_id: The golongan ID of the tunjangan if applicable.

    Returns:
        A dict containing the id, jenis_tunjangan, level_id, golongan_id, and nominal of the tunjangan.
    """
    params = {"tunjangan_id": tunjangan_id}
    query = """
            SELECT id,
                   jenis_tunjangan,
                   level_id,
                   golongan_id,
                   nominal
            FROM gaji_tunjangan
            WHERE jenis_tunjangan = %(tunjangan_id)s
            """
    if level_id in [5, 6]:
        query += " AND level_id = %(level_id)s"
        params["level_id"] = level_id
    elif golongan_id:
        query += " AND golongan_id = %(golongan_id)s"
        params["golongan_id"] = golongan_id

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
