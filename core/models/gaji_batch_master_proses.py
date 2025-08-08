import pandas as pd

from core.config import get_connection_pool, LOGGER


def delete_gaji_batch_master_proses_by_batch_master_id_list(batch_master_id_list: list[int]) -> None:
    sql = "DELETE FROM gaji_batch_master_proses WHERE batch_master_id IN %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (batch_master_id_list,))
            LOGGER.debug(f"Deleted {cursor.rowcount} gaji_batch_master_proses")
            conn.commit()


def save_gaji_batch_master_proses(df: pd.DataFrame) -> None:
    data_list = [(
        row["jenis_gaji"],
        row["formula"],
        row["kode"],
        row["nama"],
        row["nilai"],
        row["nilai_formula"],
        row["urut"],
        row["batch_master_id"],
    ) for _, row in df.iterrows()]

    query = """INSERT INTO gaji_batch_master_proses
               (jenis_gaji, formula, kode, nama, nilai, nilai_formula, urut, batch_master_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, data_list)
            LOGGER.info(f"Saved {cursor.rowcount} gaji_batch_master_proses")
            conn.commit()
