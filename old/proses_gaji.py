from datetime import time
from core.enums import STATUS_KAWIN, STATUS_PEGAWAI, TUNJANGAN, EProsesGaji
from icecream import ic
from gaji_batch_master import generate_raw_gaji_master_batch, save_gaji_batch_master
from gaji_batch_potongan_tkk import get_gaji_potongan_tkk_data
from gaji_batch_root import save_batch_root_error_logs, update_status_gaji_batch_root
from core.helper import replace_formula_with_values, safe_eval
from master_data_gaji import get_gaji_komponen_data, get_gaji_phdp_formula, get_parameter_setting_data, get_rumah_dinas_data, get_tunjangan_data

KOMPONEN_GAJI = None


def proses_detail_gaji(root_batch_id: str, row: dict):
    # setup komponen gaji
    komponen_gaji = get_gaji_komponen_data(row["gaji_profil_id"])
    maksimal_potongan_jpn = get_parameter_setting_data(
        "maksimal_potongan_jpn")["nominal"]
    maksimal_potongan_askes = get_parameter_setting_data(
        "maksimal_potongan_askes")["nominal"]
    row["org_group_id"] = row["organisasi_id"]

    komponen_gaji = setup_is_reference_nilai_formula(
        root_batch_id, komponen_gaji, row)
    komponen_gaji = setup_nilai_formula(root_batch_id, komponen_gaji, row)
    if row["nipam"] == "900800456":
        ic(komponen_gaji)
    # ic(row["tmt_kerja"], row["tmt_pensiun"])
    # pass
    pass


def setup_is_reference_nilai_formula(root_batch_id: str, komponen_gaji: list[dict], data: dict):
    index = 0
    for komponen in komponen_gaji:
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
        index += 1

    return komponen_gaji


def setup_nilai_formula(root_batch_id: str, komponen_gaji: list[dict], data_row: list[dict]):
    komponen_values = {component["kode"]: component["nilai"]
                       for component in komponen_gaji}

    index = 0
    for komponen in komponen_gaji:
        if 'formula' in komponen and komponen["formula"] not in {"#SYSTEM", ""}:
            nilai_formula = komponen['formula'].strip()
            nilai_formula = replace_formula_with_values(
                nilai_formula, komponen_values)
            try:
                nilai = safe_eval(nilai_formula)
            except Exception as error:
                ic("Error evaluating formula:", error)
                nilai = 0
            komponen["nilai_formula"] = nilai_formula
            komponen["nilai"] = nilai
        index += 1

    return komponen_gaji


# def get_ref_pot_tkk(root_batch_id: str, pegawai_id: int, nipam: str, status_pegawai: int, level_id: int = None, golongan_id: int = None):
#     jumlah_potongan = 0
#     periode = root_batch_id.split("-")[0]
#     date_until = datetime.date(int(periode[:4]), int(periode[4:6]), 20)
#     timedelta_prev_month = datetime.timedelta(days=date_until.day)
#     date_from = (date_until-timedelta_prev_month).strftime("%Y-%m-21")

#     # check Riwayat SP
#     riwayat_sp_data = get_riwayat_sp_data(
#         pegawai_id,  date_from, date_until.strftime("%Y-%m-%d"))

#     for row in riwayat_sp_data:
#         # jika pegawai kontrak kena SP 1,2,3
#         if status_pegawai == STATUS_PEGAWAI.KONTRAK.value:
#             if row["jenis_sp"] in [JENIS_SP.SP_1.value, JENIS_SP.SP_2.value, JENIS_SP.SP_3.value]:
#                 jumlah_potongan = 11
#                 break
#         if row["jenis_sp"] == JENIS_SP.SP_3.value:
#             jumlah_potongan = -1
#             break

#         jumlah_potongan += row["nilai"]

#     if jumlah_potongan > -1:
#         # check Potongan TKK
#         potongan_tkk_data = get_potongan_tkk_data(root_batch_id, nipam)
#         if potongan_tkk_data["potongan"] is not None:
#             jumlah_potongan += int(potongan_tkk_data["potongan"])

#         if status_pegawai == STATUS_PEGAWAI.PEGAWAI.value:
#             # check level between DIRUT to SPV
#             if level_id in [2, 3, 4, 5, 6]:
#                 nilai_potongan = get_gaji_potongan_tkk_data(status_pegawai=status_pegawai,
#                                                             level_id=level_id)
#             else:
#                 nilai_potongan = get_gaji_potongan_tkk_data(status_pegawai=status_pegawai,
#                                                             golongan_id=golongan_id)
#         else:
#             nilai_potongan = get_gaji_potongan_tkk_data(
#                 status_pegawai=status_pegawai)

#     pass


def validate_master_gaji(root_batch_id: str):
    update_status_gaji_batch_root(
        root_batch_id=root_batch_id, status_process=EProsesGaji.PROSES.value)
    raw_gaji_master_batch = generate_raw_gaji_master_batch()
    if raw_gaji_master_batch is None:
        return

    valid_pegawai_list = []
    error_pegawai_list = []
    total_pegawai = len(raw_gaji_master_batch),
    notes = {
        "valid": 0,
        "error": 0,
    }
    status_process = EProsesGaji.FAILED.value

    for row in raw_gaji_master_batch:
        if row["nipam"] != "900800456":
            continue
        _profil_gaji_id = row["gaji_profil_id"]
        _golongan_id = row["golongan"]
        _gaji_pokok = row["gaji_pokok"]

        if _profil_gaji_id is None:
            notes["error"] += 1
            error_pegawai_list.append({
                "root_batch_id": root_batch_id,
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "error gaji profil"
            })
            continue

        if _golongan_id is None:
            notes["error"] += 1
            error_pegawai_list.append({
                "root_batch_id": root_batch_id,
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "error golongan"
            })
            continue

        if _gaji_pokok is None or _gaji_pokok <= 0:
            notes["error"] += 1
            error_pegawai_list.append({
                "root_batch_id": root_batch_id,
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "error gaji pokok or <= 0"
            })
            continue

        # valid data gaji
        notes["valid"] += 1
        tanggungan = int(row["jml_tanggungan"])
        menikah = 1 if row["status_kawin"] == STATUS_KAWIN.KAWIN.value else 0
        jml_jiwa = 1 + tanggungan + menikah
        row["jml_jiwa"] = jml_jiwa
        valid_pegawai_list.append(row)

    save_gaji_batch_master(valid_pegawai_list, root_batch_id)
    if (notes["error"] > 0):
        update_status_gaji_batch_root(
            root_batch_id,
            status_process,
            total_pegawai,
            notes
        )
        save_batch_root_error_logs(error_pegawai_list)
        ic(error_pegawai_list)


def main():
    # KOMPONEN_GAJI = get_gaji_komponen_data()
    start=time.time()
    validate_master_gaji("202401-001")
    ic("validate finish in", time.time()-start, "seconds")

if __name__ == "__main__":
    main()
