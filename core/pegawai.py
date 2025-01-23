import pandas as pd
from core.config import get_connection_pool
from icecream import ic


def update_pegawai_tanggungan(ditanggung_list: pd.DataFrame) -> None:
    """
    Update the jml_tanggungan column in the pegawai table based on the given DataFrame.
    """
    update_data = [
        (row["jumlah_tanggungan"], row["pegawai_id"])
        for _, row in ditanggung_list.iterrows()
    ]

    query = "UPDATE pegawai SET jml_tanggungan = %s WHERE id = %s"

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, update_data)
            conn.commit()
            ic("update tanggungan pegawai ", cursor.rowcount, "affected rows")