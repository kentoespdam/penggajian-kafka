from core.config import get_connection_pool
import pandas as pd


def fetch_gaji_batch_master_proses_by_master_batch_id(master_batch_id: int) -> list:
    query = "SELECT * FROM gaji_batch_master_proses WHERE master_batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (master_batch_id,))
            return cursor.fetchall()


def delete_gaji_batch_master_proses_by_master_batch_id(master_batch_id: list) -> None:
    query = "DELETE FROM gaji_batch_master_proses WHERE master_batch_id IN %s"
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (master_batch_id,))
            connection.commit()


def save_gaji_batch_master_proses(dataframe: pd.DataFrame) -> None:
    """
    Save dataframe to gaji_batch_master_proses table.
    """
    insert_data = [
        (
            row["jenis_gaji"],
            row["formula"],
            row["kode"],
            row["nama"],
            row["nilai"],
            row["nilai_formula"],
            row["urut"],
            row["master_batch_id"],
        )
        for _, row in dataframe.iterrows()
    ]

    query = """
        INSERT INTO gaji_batch_master_proses (
            jenis_gaji, formula, kode, nama, nilai, nilai_formula, urut, master_batch_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, insert_data)
            conn.commit()


def fetch_gaji_batch_master_proses_by_master_id(master_id: int) -> list:
    query = """
        SELECT * FROM gaji_batch_master_proses gbp
        WHERE gbp.master_batch_id=%s
        """
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (master_id,))
            return cursor.fetchall()


def get_nilai_komponen(daftar_proses_gaji_pegawai: pd.DataFrame, master_batch_id: int, kode: str):
    result = daftar_proses_gaji_pegawai[(daftar_proses_gaji_pegawai["master_batch_id"] == master_batch_id) & (
        daftar_proses_gaji_pegawai["kode"] == kode)]
    return result["nilai"].values[0] if not result.empty else 0


def get_total_nilai_komponen(salary_components: pd.DataFrame, component_code: str) -> float:
    return salary_components[salary_components["kode"] == component_code]["nilai"].sum()
