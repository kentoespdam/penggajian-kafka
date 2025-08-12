from core.config import get_connection_pool, LOGGER
from core.enums import STATUS_KERJA
import pandas as pd


def delete_gaji_batch_master_by_batch_root_id(batch_root_id: str) -> None:
    query = "DELETE FROM gaji_batch_master WHERE batch_root_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (batch_root_id,))
            conn.commit()


def fetch_raw_gaji_master_batch():
    sql = """
          SELECT peg.id                        AS pegawai_id,
                 peg.nipam,
                 bio.nama,
                 IFNULL(peg.golongan_id, 0)    AS golongan_id,
                 gol.pangkat,
                 gol.golongan,
                 peg.jabatan_id,
                 jab.nama                      AS nama_jabatan,
                 jab.level_id,
                 peg.organisasi_id,
                 org.nama                      AS nama_organisasi,
                 peg.status_pegawai,
                 IFNULL(peg.gaji_profil_id, 0) AS gaji_profil_id,
                 IFNULL(peg.gaji_pokok, 0)     AS gaji_pokok,
                 peg.phdp,
                 bio.status_kawin,
                 IFNULL(peg.jml_tanggungan, 0) AS jml_tanggungan,
                 0                             AS jml_jiwa,
                 peg.gaji_pendapatan_non_pajak_id,
                 gpn.kode                      AS kode_pajak,
                 peg.rumah_dinas_id
          FROM pegawai AS peg
                   INNER JOIN biodata bio ON peg.nik = bio.nik
                   LEFT JOIN golongan gol ON peg.golongan_id = gol.id
                   LEFT JOIN organisasi org ON peg.organisasi_id = org.id
                   LEFT JOIN jabatan jab ON peg.jabatan_id = jab.id
                   LEFT JOIN gaji_pendapatan_non_pajak gpn ON peg.gaji_pendapatan_non_pajak_id = gpn.id
          WHERE peg.is_deleted = FALSE
            AND peg.status_kerja = %s
          """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (STATUS_KERJA.KARYAWAN_AKTIF.value,))
            return pd.DataFrame(cursor.fetchall())


def save_gaji_batch_master(data: pd.DataFrame) -> None:
    update_data = [(
        row["batch_root_id"],
        row["periode"],
        row["pegawai_id"],
        row["nipam"],
        row["nama"],
        row["golongan_id"] if row["golongan_id"] > 0 else None,
        row["golongan"],
        row["pangkat"],
        row["jabatan_id"],
        row["nama_jabatan"],
        row["level_id"],
        row["organisasi_id"],
        row["nama_organisasi"],
        row["status_pegawai"],
        row["gaji_profil_id"],
        row["gaji_pokok"],
        row["phdp"],
        row["status_kawin"],
        row["jml_tanggungan"],
        row["gaji_pendapatan_non_pajak_id"],
        row["kode_pajak"],
        row["jml_jiwa"],
        row["penghasilan_kotor"],
        row["total_potongan"],
        row["total_add_tambahan"],
        row["total_add_potongan"],
        row["penghasilan_bersih"],
        row["pembulatan"],
        row["penghasilan_bersih_final"],
        row["pajak"],
        False,
    ) for _, row in data.iterrows()]

    query = """
            INSERT INTO gaji_batch_master (batch_root_id, periode, pegawai_id, nipam, nama,
                                           golongan_id, golongan, pangkat, jabatan_id, nama_jabatan,
                                           level_id, organisasi_id, nama_organisasi, status_pegawai, gaji_profil_id,
                                           gaji_pokok, phdp, status_kawin, jml_tanggungan, gaji_pendapatan_non_pajak_id,
                                           kode_pajak, jml_jiwa, penghasilan_kotor, total_potongan, total_add_tambahan,
                                           total_add_potongan, penghasilan_bersih, pembulatan, penghasilan_bersih_final,
                                           pajak,
                                           is_different)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s)
            """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, update_data)
            LOGGER.info(f"{cursor.rowcount} rows inserted")
            conn.commit()


def fetch_gaji_batch_master_data_by_batch_root_id(root_batch_id: str) -> pd.DataFrame:
    sql = """
          SELECT gbm.id,
                 gbm.batch_root_id,
                 gbm.pegawai_id,
                 gbm.nipam,
                 gbm.nama,
                 peg.status_pegawai,
                 gbm.gaji_pokok,
                 gbm.phdp,
                 IFNULL(gbm.golongan_id, 0) AS golongan_id,
                 gbm.level_id,
                 gbm.gaji_profil_id,
                 gbm.kode_pajak,
                 gbm.jml_jiwa,
                 gbm.jml_tanggungan,
                 gbm.status_kawin,
                 peg.is_askes,
                 peg.rumah_dinas_id,
                 gbm.penghasilan_kotor,
                 gbm.total_potongan,
                 gbm.total_add_tambahan,
                 gbm.total_add_potongan,
                 gbm.penghasilan_bersih,
                 gbm.penghasilan_bersih2,
                 gbm.pembulatan,
                 gbm.pembulatan2,
                 gbm.penghasilan_bersih_final,
                 gbm.penghasilan_bersih_final2,
                 gbm.pajak
          FROM gaji_batch_master AS gbm
                   LEFT JOIN pegawai AS peg ON gbm.pegawai_id = peg.id
          WHERE gbm.batch_root_id = %s
          """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (root_batch_id,))
            return pd.DataFrame(cursor.fetchall())


def fetch_gaji_batch_master_by_periode(periode: str) -> pd.DataFrame:
    sql = """
          SELECT gbm.id,
                 gbm.batch_root_id,
                 gbm.pegawai_id,
                 gbm.nipam,
                 gbm.nama,
                 gbm.gaji_pokok,
                 gbm.golongan_id,
                 gbm.jml_jiwa,
                 gbm.jml_tanggungan,
                 gbm.kode_pajak,
                 gbm.level_id,
                 gbm.phdp,
                 gbm.status_kawin,
                 gbm.status_pegawai,
                 gbm.gaji_profil_id,
                 gbm.jabatan_id,
                 gbm.organisasi_id,
                 gbm.penghasilan_kotor,
                 gbm.total_potongan,
                 gbm.total_add_tambahan,
                 gbm.total_add_potongan,
                 gbm.penghasilan_bersih,
                 gbm.pembulatan,
                 gbm.penghasilan_bersih_final,
                 peg.rumah_dinas_id,
                 peg.is_askes
          FROM gaji_batch_master AS gbm
                   LEFT JOIN
               pegawai AS peg
               ON gbm.pegawai_id = peg.id
          WHERE gbm.periode = %s
          """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (periode,))
            return pd.DataFrame(cursor.fetchall())


def reset_different_gaji_as_false(root_batch_id: str) -> None:
    sql = "UPDATE gaji_batch_master SET is_different = FALSE WHERE batch_root_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (root_batch_id,))
            conn.commit()


def update_different_gaji(difference_gaji: list) -> None:
    query = "UPDATE gaji_batch_master SET is_different = true WHERE batch_root_id = %s AND pegawai_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, difference_gaji)
            LOGGER.info(f"{cursor.rowcount} rows updated")
            conn.commit()


def update_gaji_batch_master(df: pd.DataFrame) -> None:
    update_data = [(
        row.penghasilan_kotor,
        row.total_potongan,
        row.total_add_tambahan,
        row.total_add_potongan,
        row.penghasilan_bersih,
        row.penghasilan_bersih2,
        row.pembulatan,
        row.pembulatan2,
        row.penghasilan_bersih_final,
        row.penghasilan_bersih_final2,
        row.pajak,
        row.id,
    ) for row in df.itertuples()]

    query = """
            UPDATE gaji_batch_master
            SET penghasilan_kotor         = %s,
                total_potongan            = %s,
                total_add_tambahan        = %s,
                total_add_potongan        = %s,
                penghasilan_bersih        = %s,
                penghasilan_bersih2       = %s,
                pembulatan                = %s,
                pembulatan2               = %s,
                penghasilan_bersih_final  = %s,
                penghasilan_bersih_final2 = %s,
                pajak                     = %s
            WHERE id = %s
            """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, update_data)
            LOGGER.info(f"{cursor.rowcount} rows updated")
            conn.commit()


def fetch_daftar_gaji_pegawai(batch_root_id: str):
    query = """
            SELECT gbm.id,
                   gbm.nipam,
                   gbm.nama,
                   gbm.status_pegawai,
                   gbm.gaji_pokok,
                   org.id   AS organisasi_id,
                   org.kode AS kode_organisasi,
                   org.nama AS nama_organisasi,
                   gbm.golongan_id,
                   gbm.golongan,
                   gbm.pangkat,
                   gbm.level_id,
                   gbm.jml_jiwa,
                   gbm.jml_tanggungan,
                   gbm.status_kawin,
                   gbm.penghasilan_kotor,
                   gbm.total_potongan,
                   gbm.total_add_tambahan,
                   gbm.total_add_potongan,
                   gbm.penghasilan_bersih,
                   gbm.pembulatan,
                   gbm.penghasilan_bersih_final,
                   gbm.is_different,
                   gbp.batch_master_id,
                   gbp.kode,
                   gbp.jenis_gaji,
                   gbp.nilai,
                   gbp.nama AS uraian
            FROM gaji_batch_master AS gbm
                     INNER JOIN pegawai AS peg ON gbm.pegawai_id = peg.id
                     INNER JOIN gaji_batch_master_proses gbp ON gbm.id = gbp.batch_master_id
                     INNER JOIN organisasi AS org ON gbm.organisasi_id = org.id
            WHERE gbm.batch_root_id = %s
            """

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (batch_root_id,))
            return pd.DataFrame(cursor.fetchall())


def fetch_daftar_potongan_gaji_by_batch_root_id(batch_root_id: str) -> pd.DataFrame:
    query = """
            SELECT gbm.id,
                   gbm.nipam,
                   gbm.nama,
                   gbm.level_id,
                   org.kode AS kode_organisasi,
                   gbm.penghasilan_bersih
            FROM gaji_batch_master AS gbm
                     INNER JOIN organisasi AS org ON gbm.organisasi_id = org.id
            WHERE gbm.batch_root_id = %s
            """

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (batch_root_id,))
            return pd.DataFrame(cursor.fetchall())
