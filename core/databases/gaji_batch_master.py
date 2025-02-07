from core.config import get_connection_pool
from core.enums import STATUS_KERJA
import pandas as pd
from icecream import ic


def fetch_raw_gaji_master_batch() -> list:
    sql = """
        SELECT
            peg.id AS pegawai_id,
            peg.nipam,
            bio.nama,
            peg.golongan_id,
            gol.pangkat,
            gol.golongan,
            peg.jabatan_id,
            jab.nama AS nama_jabatan,
            jab.level_id,
            peg.organisasi_id,
            org.nama AS nama_organisasi,
            peg.status_pegawai,
            peg.gaji_profil_id,
            peg.gaji_pokok,
            peg.phdp,
            bio.status_kawin,
            IFNULL(peg.jml_tanggungan, 0) AS jml_tanggungan,
            0 AS jml_jiwa,
            peg.gaji_pendapatan_non_pajak_id,
            gpn.kode AS kode_pajak,
            peg.rumah_dinas_id
        FROM
            pegawai AS peg
            INNER JOIN biodata bio ON peg.nik = bio.nik
            LEFT JOIN golongan gol ON peg.golongan_id=gol.id
            LEFT JOIN organisasi org ON peg.organisasi_id=org.id
            LEFT JOIN jabatan jab ON peg.jabatan_id=jab.id
            LEFT JOIN gaji_pendapatan_non_pajak gpn ON peg.gaji_pendapatan_non_pajak_id=gpn.id
        WHERE
            peg.is_deleted = FALSE
            AND peg.status_kerja = %s
            -- AND peg.nipam IN ('690700169', '660600242')
            -- AND peg.nipam IN ('900800456','641100143','KO-329')
            -- AND peg.nipam IN ('730800368')
        """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (STATUS_KERJA.KARYAWAN_AKTIF.value,))
            return cursor.fetchall()


def fetch_gaji_batch_master_data_by_root_batch_id(root_batch_id: str) -> list:
    query = """
        SELECT
            gbm.id,
            gbm.root_batch_id, 
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
            gbm.total_tambahan, 
            gbm.total_potongan, 
            gbm.pembulatan, 
            gbm.penghasilan_bersih, 
            peg.rumah_dinas_id,
            peg.is_askes
        FROM
            gaji_batch_master AS gbm
            LEFT JOIN
            pegawai AS peg
            ON gbm.pegawai_id = peg.id
        WHERE 
            gbm.root_batch_id = %s
    """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            return cursor.fetchall()


def fetch_gaji_batch_master_by_periode(periode: str) -> list:
    query = """
        SELECT
            gbm.id,
            gbm.root_batch_id, 
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
            gbm.total_tambahan, 
            gbm.total_potongan, 
            gbm.pembulatan, 
            gbm.penghasilan_bersih, 
            peg.rumah_dinas_id,
            peg.is_askes
        FROM
            gaji_batch_master AS gbm
            LEFT JOIN
            pegawai AS peg
            ON gbm.pegawai_id = peg.id
        WHERE 
            gbm.periode = %s
    """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (periode,))
            return cursor.fetchall()

def delete_gaji_batch_master_by_root_batch_id(root_batch_id: str) -> None:
    query = "DELETE FROM gaji_batch_master WHERE root_batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            conn.commit()


def save_gaji_batch_master(data: pd.DataFrame) -> None:
    update_data = [(
        row["root_batch_id"],
        row["periode"],
        row["pegawai_id"],
        row["nipam"],
        row["nama"],
        row["golongan_id"] if not pd.isna(row["golongan_id"]) else None,
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
        row["created_by"],
        row["updated_by"],
        row["penghasilan_kotor"],
        row["total_tambahan"],
        row["total_potongan"],
        row["pembulatan"],
        row["penghasilan_bersih"],
    ) for _, row in data.iterrows()]

    query = """
        INSERT INTO gaji_batch_master (
            root_batch_id, periode, pegawai_id, nipam, nama,
            golongan_id, golongan, pangkat, jabatan_id, nama_jabatan,
            level_id, organisasi_id, nama_organisasi, status_pegawai, gaji_profil_id,
            gaji_pokok, phdp, status_kawin, jml_tanggungan, gaji_pendapatan_non_pajak_id, kode_pajak, 
            jml_jiwa, created_by, updated_by, penghasilan_kotor, total_tambahan, 
            total_potongan, pembulatan, penghasilan_bersih
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, update_data)
            conn.commit()
            ic("update gaji batch master ", cursor.rowcount, "affected rows")


def update_gaji_batch_master(data: pd.DataFrame) -> None:
    update_data = [(
        row["penghasilan_kotor"],
        row["total_tambahan"],
        row["total_potongan"],
        row["pembulatan"],
        row["penghasilan_bersih"],
        row["id"],
    ) for _, row in data.iterrows()]

    query = """
            UPDATE gaji_batch_master SET
                penghasilan_kotor = %s,
                total_tambahan = %s,
                total_potongan = %s,
                pembulatan = %s,
                penghasilan_bersih = %s
            WHERE id = %s
        """

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, update_data)
            conn.commit()
            ic("update gaji batch master ", cursor.rowcount, "affected rows")


def reset_different_gaji_batch_master_as_false(root_batch_id: str) -> None:
    query = "UPDATE gaji_batch_master SET is_different = false WHERE root_batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            conn.commit()


def update_different_gaji_batch_master(data: list) -> None:
    query = "UPDATE gaji_batch_master SET is_different = true WHERE root_batch_id = %s AND pegawai_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, data)
            conn.commit()
