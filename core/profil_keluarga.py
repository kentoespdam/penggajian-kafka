from core.config import get_connection_pool
from core.enums import HUBUNGAN_KELUARGA, STATUS_KERJA
from icecream import ic
import pandas as pd


def fetch_tanggungan_list(pegawai_id: int = None):
    params = (STATUS_KERJA.KARYAWAN_AKTIF.value,
              STATUS_KERJA.DIRUMAHKAN.value,
              HUBUNGAN_KELUARGA.ANAK.value)
    query = """
        SELECT
            p.id AS pegawai_id,
            pk.id,
            pk.status_kawin,
            pk.status_pendidikan,
            TIMESTAMPDIFF(
                YEAR,
                pk.tanggal_lahir,
                CURRENT_DATE
            ) AS umur
        FROM
            profil_keluarga pk
            INNER JOIN pegawai p
                ON pk.biodata_id = p.nik
                AND p.is_deleted = FALSE
                AND p.status_kerja IN (%s, %s)
        WHERE
            pk.is_deleted = FALSE
            AND pk.hubungan_keluarga = %s
        """
    if pegawai_id:
        query += " AND p.id = %s"
        params = params + (pegawai_id,)

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def update_tanggungan_status(tanggungan_df: pd.DataFrame) -> None:
    """
    Update the tanggungan status in the database based on the given DataFrame.

    Args:
        tanggungan_df: A DataFrame containing the updated tanggungan status.
    """
    data_to_update = [(row["tanggungan"], row["id"])
                      for _, row in tanggungan_df.iterrows()]
    query = "UPDATE profil_keluarga SET tanggungan = %s WHERE id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, data_to_update)
            conn.commit()
            ic("update profil keluarga ", cursor.rowcount, "affected rows")
