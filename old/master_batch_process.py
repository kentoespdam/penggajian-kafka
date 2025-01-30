from core.enums import STATUS_KAWIN, STATUS_PEGAWAI, TUNJANGAN
from gaji_batch_master import get_gaji_batch_master_data
from icecream import ic

from gaji_batch_potongan_tkk import get_gaji_potongan_tkk_data
from master_data_gaji import get_gaji_komponen_data, get_gaji_phdp_formula, get_rumah_dinas_data, get_tunjangan_data


def process_master_batch(root_batch_id: str) -> None:
    """
    Process a batch of employees' salaries.

    Args:
        root_batch_id (str): The root batch ID.
    """
    gaji_batch_master_data = get_gaji_batch_master_data(root_batch_id)

    if not gaji_batch_master_data:
        return

    for data in gaji_batch_master_data:
        # setup komponen gaji
        komponen_gaji = get_gaji_komponen_data(data["gaji_profil_id"])
        komponen_gaji = setup_nilai_referensi_komponen_gaji(root_batch_id, komponen_gaji, data)


def setup_nilai_referensi_komponen_gaji(root_batch_id: str, komponen_gaji: list, data: dict):
    for index, komponen in enumerate(komponen_gaji):
        if komponen["is_reference"] == False:
            continue
        if komponen["kode"] == "GP":
            komponen["nilai"] = data["gaji_pokok"]
        elif komponen["kode"] == "JML_ANAK":
            komponen["nilai"] = data["jml_tanggungan"]
        elif komponen["kode"] == "JML_JIWA":
            tanggungan = int(data["jml_tanggungan"])
            menikah = 1 if data["status_kawin"] == STATUS_KAWIN.KAWIN.value else 0
            jml_jiwa = 1 + tanggungan + menikah
            komponen["nilai"] = jml_jiwa
        elif komponen["kode"] == "REF_TUNJ_JABATAN":
            if data["status_pegawai"] in [STATUS_PEGAWAI.KONTRAK.value, STATUS_PEGAWAI.CALON_HONORER.value] or int(data["level_id"]) in [2, 3, 4]:
                komponen["nilai"] = 0
            else:
                nominal = get_tunjangan_data(
                    TUNJANGAN.JABATAN.value,
                    data["level_id"],
                    data["golongan_id"]
                )["nominal"]
                komponen["nilai"] = nominal
        elif komponen["kode"] == "REF_TUNJ_BERAS":
            if data["status_pegawai"] in [STATUS_PEGAWAI.KONTRAK.value, STATUS_PEGAWAI.CALON_HONORER.value] or int(data["level_id"]) in [2, 3, 4]:
                komponen["nilai"] = 0
            else:
                nominal = get_tunjangan_data(
                    reference=TUNJANGAN.BERAS.value,
                    golongan_id=data["golongan_id"]
                )["nominal"]
                komponen["nilai"] = nominal
        elif komponen["kode"] == "REF_TUNJ_KK":
            if data["status_pegawai"] in [STATUS_PEGAWAI.KONTRAK.value, STATUS_PEGAWAI.CALON_HONORER.value] or int(data["level_id"]) in [2, 3, 4]:
                komponen["nilai"] = 0
            else:
                nominal = get_tunjangan_data(
                    TUNJANGAN.KINERJA.value,
                    data["level_id"],
                    data["golongan_id"]
                )["nominal"]
                komponen["nilai"] = nominal
        elif komponen["kode"] == "REF_TUNJ_AIR":
            if data["status_pegawai"] in [STATUS_PEGAWAI.KONTRAK.value, STATUS_PEGAWAI.CALON_HONORER.value] or int(data["level_id"]) in [2, 3, 4]:
                komponen["nilai"] = 0
            else:
                nominal = get_tunjangan_data(
                    TUNJANGAN.AIR.value,
                    data["level_id"],
                    data["golongan_id"]
                )["nominal"]
                komponen["nilai"] = nominal
        elif komponen["kode"] == "REF_PHDP":
            formula = get_gaji_phdp_formula(
                data["tmt_kerja"], data["tmt_pensiun"])
            komponen["formula"] = formula
            komponen["nilai"] = 0
        elif komponen["kode"] == "REF_SEWA_RUMDIN":
            if data["rumah_dinas_id"] is None or data["rumah_dinas_id"] == 0:
                komponen["nilai"] = 0
                continue
            nominal = get_rumah_dinas_data(data["rumah_dinas_id"])["nominal"]
            komponen["nilai"] = nominal
        elif komponen["kode"] == "REF_POT_TKK":
            if data["status_pegawai"] == STATUS_PEGAWAI.PEGAWAI.value:
                # check level between DIRUT to SPV
                if data["level_id"] in [2, 3, 4, 5, 6]:
                    nominal = get_gaji_potongan_tkk_data(status_pegawai=data["status_pegawai"],
                                                         level_id=data["level_id"])
                else:
                    nominal = get_gaji_potongan_tkk_data(status_pegawai=data["status_pegawai"],
                                                         golongan_id=data["golongan_id"])
            else:
                nominal = get_gaji_potongan_tkk_data(
                    status_pegawai=data["status_pegawai"])
            komponen["nilai"] = nominal["nominal"]
        komponen_gaji[index] = komponen


if __name__ == "__main__":
    process_master_batch("202401-001")
