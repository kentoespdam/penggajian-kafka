import pandas as pd
import swifter  # noqa: F401
from icecream import ic

from config import ENGINE
from enums import STATUS_KAWIN, STATUS_KERJA


def ambil_data_pegawai():
    sql = """
        SELECT
            peg.id,
            peg.nipam,
            bio.nama,
            peg.golongan_id,
            gol.pangkat,
            gol.golongan,
            peg.jabatan_id,
            jab.nama AS jabatan,
            peg.organisasi_id,
            org.nama AS organisasi,
            peg.status_pegawai,
            peg.gaji_profil_id,
            peg.gaji_pokok,
            bio.status_kawin,
            IFNULL(peg.jml_tanggungan, 0) AS jml_tanggungan,
            0 AS jml_jiwa,
            peg.gaji_pendapatan_non_pajak_id
        FROM
            pegawai AS peg
            INNER JOIN biodata bio ON peg.biodata_id = bio.nik 
            JOIN golongan gol ON peg.golongan_id=gol.id
            JOIN organisasi org ON peg.organisasi_id=org.id
            JOIN jabatan jab ON peg.jabatan_id=jab.id
        WHERE
            peg.is_deleted = FALSE 
            AND peg.status_kerja = %s
        """
    params = [STATUS_KERJA.KARYAWAN_AKTIF.value]
    data = pd.read_sql(sql, con=ENGINE, params=tuple(params))
    data["jml_jiwa"] = data.swifter.apply(
        lambda row: (
            row["jml_tanggungan"] + 1
            if row["status_kawin"] == STATUS_KAWIN.KAWIN.value
            else row["jml_tanggungan"]
        ),
        axis=1,
    )

    # ic(data.to_dict("records"))
    return data


def phase1(data: pd.DataFrame):
    status_counts = {
        "success": 0,
        "error_missing_gaji_profil": 0,
        "error_missing_golongan": 0,
    }

    valid_entries = []

    for _, row in data.iterrows():
        ic(row["gaji_profil_id"].isnull())
        continue
        # if row["gaji_profil_id"] is None:
        #     status_counts["error_missing_gaji_profil"] += 1
        #     continue

        # if row["golongan"] is None:
        #     status_counts["error_missing_golongan"] += 1
        #     continue

        # valid_entries.append(row)
        # status_counts["success"] += 1

    valid_data = pd.DataFrame(valid_entries)
    return valid_data, status_counts


if __name__ == "__main__":
    data_pegawai = ambil_data_pegawai()
    valida_data, status_counts = phase1(data_pegawai)
    ic(valida_data.to_dict("records"))