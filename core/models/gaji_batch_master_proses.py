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


def fetch_gaji_batch_master_proses_by_root_batch_id(root_batch_id: str) -> pd.DataFrame:
    query = """SELECT gbp.id,
                      gbp.batch_master_id,
                      gbp.formula,
                      gbp.jenis_gaji,
                      gbp.kode,
                      gbp.nama,
                      gbp.nilai,
                      gbp.nilai_formula,
                      gbp.urut
               FROM gaji_batch_master AS gbm
                        INNER JOIN gaji_batch_root AS gbr ON gbm.batch_root_id = gbr.id
                   AND gbr.is_deleted = 0
                        INNER JOIN gaji_batch_master_proses AS gbp ON gbp.batch_master_id = gbm.id
               WHERE gbr.id = %s
            """
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            return pd.DataFrame(cursor.fetchall())


def rollback_additional_gaji_batch_master_proses(batch_master_id: int = None) -> None:
    query = "DELETE FROM gaji_batch_master_proses WHERE kode LIKE %s"
    params = ("ADD_%",)
    if batch_master_id:
        query += " AND batch_master_id = %s"
        params += (batch_master_id,)

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()


def fetch_additional_gaji_batch_master_proses_by_periode(periode: str) -> pd.DataFrame:
    query = """
        SELECT
            gbp.id,
            gbp.batch_master_id,
            gbp.kode,
            gbp.nama,
            gbp.nilai,
            gmb.nipam 
        FROM
            gaji_batch_master_proses AS gbp
            INNER JOIN gaji_batch_master AS gmb ON gbp.batch_master_id = gmb.id
            INNER JOIN gaji_batch_root AS gbr ON gmb.batch_root_id = gbr.id 
        WHERE
            gbr.periode = %s 
            AND gbr.is_deleted = %s 
            AND gbr.`status` > %s 
            AND gbp.kode LIKE %s
        ORDER BY
            gbp.id ASC
        """
    params = (periode, False, 1, "ADD_%")
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return pd.DataFrame(cursor.fetchall())
