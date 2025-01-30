import datetime

from core.config import POOL
from core.enums import STATUS_KERJA
from icecream import ic

def get_gaji_batch_master_data(root_batch_id: str) -> list:
    """
    Fetch GajiBatchMaster data by root batch ID.
    Args:
        root_batch_id (str): Root batch ID.
    Returns:
        list: List of GajiBatchMaster data.
    """
    query = """
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
            bio.status_kawin,
            IFNULL(peg.jml_tanggungan, 0) AS jml_tanggungan,
            0 AS jml_jiwa,
            peg.gaji_pendapatan_non_pajak_id,
            gpn.kode AS kode_pajak,
            peg.rumah_dinas_id,
            peg.tmt_kerja,
            peg.tmt_pensiun
        FROM
            pegawai AS peg
            INNER JOIN biodata bio ON peg.nik = bio.nik
            LEFT JOIN golongan gol ON peg.golongan_id=gol.id
            LEFT JOIN organisasi org ON peg.organisasi_id=org.id
            LEFT JOIN jabatan jab ON peg.jabatan_id=jab.id
            LEFT JOIN gaji_pendapatan_non_pajak gpn ON peg.gaji_pendapatan_non_pajak_id=gpn.id
        WHERE 
            root_batch_id = %s
    """
    with POOL.get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            data = cursor.fetchall()
    return data


def generate_raw_gaji_master_batch():
    data = None
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
            bio.status_kawin,
            IFNULL(peg.jml_tanggungan, 0) AS jml_tanggungan,
            0 AS jml_jiwa,
            peg.gaji_pendapatan_non_pajak_id,
            gpn.kode AS kode_pajak,
            peg.rumah_dinas_id,
            peg.tmt_kerja,
            peg.tmt_pensiun
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
            AND peg.nipam='900800456'
        """

    try:
        with POOL.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (STATUS_KERJA.KARYAWAN_AKTIF.value,))
                data = cursor.fetchall()
    except Exception as e:
        ic("""error generate_raw_gaji_master_batch""", e)

    return data


def save_gaji_batch_master(data: dict, root_batch_id: str):
    prepared_data = prepare_gaji_batch_data(data, root_batch_id)
    sql = """
        INSERT INTO gaji_batch_master (
            root_batch_id, 
            periode, 
            pegawai_id, 
            nipam, 
            nama, 
            golongan_id,
            golongan,
            pangkat,
            jabatan_id,
            nama_jabatan,
            level_id,
            organisasi_id,
            nama_organisasi,
            status_pegawai,
            gaji_profil_id,
            gaji_pokok,
            status_kawin,
            jml_tanggungan,
            kode_pajak,
            jml_jiwa,
            created_at,
            updated_at,
            created_by,
            updated_by,
            penghasilan_kotor,
            total_tambahan,
            total_potongan,
            pembulatan,
            penghasilan_bersih
        ) VALUES (
            %(root_batch_id)s,
            %(periode)s,
            %(pegawai_id)s,
            %(nipam)s,
            %(nama)s,
            %(golongan_id)s,
            %(golongan)s,
            %(pangkat)s,
            %(jabatan_id)s,
            %(nama_jabatan)s,
            %(level_id)s,
            %(organisasi_id)s,
            %(nama_organisasi)s,
            %(status_pegawai)s,
            %(gaji_profil_id)s,
            %(gaji_pokok)s,
            %(status_kawin)s,
            %(jml_tanggungan)s,
            %(kode_pajak)s,
            %(jml_jiwa)s,
            %(created_at)s,
            %(updated_at)s,
            %(created_by)s,
            %(updated_by)s,
            %(penghasilan_kotor)s,
            %(total_tambahan)s,
            %(total_potongan)s,
            %(pembulatan)s,
            %(penghasilan_bersih)s
        )
        """

    try:
        with POOL.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(sql, prepared_data)
                conn.commit()
    except Exception as e:
        ic("""error save_gaji_batch_master""", e)


def prepare_gaji_batch_data(list: list, root_batch_id: str):
    for index, data in enumerate(list):
        data["root_batch_id"] = root_batch_id
        data["periode"] = root_batch_id.split("-")[0]
        data["created_at"] = datetime.date.today()
        data["updated_at"] = datetime.date.today()
        data["created_by"] = "system"
        data["updated_by"] = "system"
        data["penghasilan_kotor"] = 0
        data["total_tambahan"] = 0
        data["total_potongan"] = 0
        data["pembulatan"] = 0
        data["penghasilan_bersih"] = 0
        list[index] = data
    return list