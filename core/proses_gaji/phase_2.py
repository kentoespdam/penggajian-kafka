import datetime

from core.config import log_debug, log_error, log_info
from core.databases.gaji_batch_master import fetch_gaji_batch_master_by_periode, fetch_gaji_batch_master_data_by_root_batch_id, reset_different_gaji_batch_master_as_false, update_different_gaji_batch_master, update_gaji_batch_master
from core.databases.gaji_batch_master_proses import delete_gaji_batch_master_proses_by_master_batch_id, save_gaji_batch_master_proses
from core.databases.gaji_batch_root import fetch_gaji_batch_root_by_batch_id, update_status_gaji_batch_root
from core.databases.gaji_komponen import fetch_gaji_komponen
from icecream import ic
import pandas as pd

from core.databases.gaji_batch_potongan_tkk import calculate_jml_pot_tkk, fetch_all_gaji_batch_potongan_tkk_by_root_batch_id, fetch_all_gaji_potongan_tkk, filter_gaji_potongan_tkk
from core.databases.gaji_parameter import fetch_parameter_setting_data
from core.databases.gaji_pendapatan_non_pajak import fetch_all_gaji_pendapatan_non_pajak, filter_gaji_pendapatan_non_pajak
from core.databases.gaji_tunjangan import fetch_all_tunjangan_data, filter_tunjangan_data
from core.databases.riwayat_sp import fetch_all_riwayat_sp_by_date
from core.databases.rumah_dinas import fetch_all_rumah_dinas, filter_rumah_dinas_by_id
from core.enums import STATUS_KAWIN, TUNJANGAN, EProsesGaji
from core.helper import replace_formula_to_variable, replace_formula_with_values, safe_eval

"""
    Todo Phase 2:
    - fetch gaji batch master
    - calculate komponen gaji
    - update gaji batch master
"""


def calculate_gaji_detail(root_batch_id: str) -> bool:
    """
    Calculate komponen gaji detail for given root batch ID.

    Args:
        root_batch_id (str): Root batch ID.

    Returns:
        bool: True if success, False if failed.
    """
    log_info(f"calculate gaji detail {root_batch_id}\n")
    gaji_batch_master_data = pd.DataFrame(
        fetch_gaji_batch_master_data_by_root_batch_id(root_batch_id))

    if gaji_batch_master_data.empty:
        return False

    gaji_batch_master_data["is_askes"] = gaji_batch_master_data["is_askes"].apply(
        lambda x: False if x is None else bool(int.from_bytes(x, "little")))

    gbm = processing_gaji_komponen_detail(
        root_batch_id, gaji_batch_master_data)

    compare_with_latest_gaji(root_batch_id, gbm)
    update_gaji_batch_master(gbm)


    gaji_batch_root=fetch_gaji_batch_root_by_batch_id(root_batch_id)
    update_status_gaji_batch_root(
        root_batch_id=root_batch_id, 
        status_process=EProsesGaji.WAIT_VERIFICATION_PHASE_1.value,
        total_pegawai=gaji_batch_root["total_pegawai"],
        notes=gaji_batch_root["notes"]
    )
    return True


def processing_gaji_komponen_detail(root_batch_id: str, gaji_batch_master_data: pd.DataFrame) -> pd.DataFrame:
    """
    Set up gaji komponen detail for given gaji batch master data.

    Args:
        gaji_batch_master_data (pd.DataFrame): Gaji batch master data.
    """
    log_debug("Setting up gaji komponen detail")
    gbm, mbp = generate_gaji_batch_master_proses_data(
        root_batch_id, gaji_batch_master_data)

    gbm["penghasilan_kotor"] = gbm.apply(lambda x: filter_komponen_by_kode(
        mbp, "PENGHASILAN_KOTOR", x["id"])["nilai"].sum(), axis=1)
    gbm["total_potongan"] = gbm.apply(lambda x: filter_komponen_by_kode(
        mbp, "POTONGAN", x["id"])["nilai"].sum(), axis=1)
    gbm["pembulatan"] = gbm.apply(lambda x: filter_komponen_by_kode(
        mbp, "PEMBULATAN", x["id"])["nilai"].sum(), axis=1)
    gbm["penghasilan_bersih"] = gbm.apply(lambda x: filter_komponen_by_kode(
        mbp, "PENGHASILAN_BERSIH_FINAL", x["id"])["nilai"].sum(), axis=1)

    list_master_row_id = mbp["master_batch_id"].unique(
    ).tolist()
    # save komponen_df to database
    delete_gaji_batch_master_proses_by_master_batch_id(list_master_row_id)
    save_gaji_batch_master_proses(mbp)
    return gbm


def filter_komponen_by_kode(komponen: pd.DataFrame, kode: str, master_batch_id: int):
    return komponen[(komponen["kode"] == kode) & (komponen["master_batch_id"] == master_batch_id)].reset_index(drop=True)


def filter_komponen_by_jenis_gaji(komponen: pd.DataFrame, jenis_gaji: str, master_batch_id: int):
    result = komponen[(komponen["jenis_gaji"] == jenis_gaji) & (
        komponen["master_batch_id"] == master_batch_id) & (komponen["kode"] != "GP")].reset_index(drop=True)
    ic(result[["kode", "jenis_gaji", "nilai"]])
    return result


def generate_gaji_batch_master_proses_data(root_batch_id: str, gaji_batch_master_data: pd.DataFrame):
    maksimal_potongan = {
        "jpn": fetch_parameter_setting_data("maksimal_potongan_jpn")["nominal"],
        "askes": fetch_parameter_setting_data("maksimal_potongan_askes")["nominal"]
    }
    all_komponen_gaji = pd.DataFrame(fetch_gaji_komponen())
    tunjangan_data = pd.DataFrame(fetch_all_tunjangan_data())
    rumah_dinas_data = pd.DataFrame(fetch_all_rumah_dinas())
    gaji_potongan_data = pd.DataFrame(fetch_all_gaji_potongan_tkk())

    # get data riwayat SP
    periode = root_batch_id.split("-")[0]
    date_until = datetime.date(int(periode[0:4]), int(periode[4:6]), 20)
    timedelta_prev_month = datetime.timedelta(days=date_until.day)
    date_from = (date_until-timedelta_prev_month).strftime("%Y-%m-21")
    riwayat_sp_data = pd.DataFrame(
        fetch_all_riwayat_sp_by_date(date_from, date_until))
    gaji_potongan_tkk_data = pd.DataFrame(
        fetch_all_gaji_batch_potongan_tkk_by_root_batch_id(root_batch_id))

    gaji_pendapatan_non_pajak_data = pd.DataFrame(
        fetch_all_gaji_pendapatan_non_pajak())
    result_komponen_list = pd.DataFrame()
    for _, master_row in gaji_batch_master_data.iterrows():
        log_debug(f"Processing gaji komponen detail for {
            master_row['nipam']} - {master_row['nama']} - [{master_row["status_pegawai"]}] - {master_row['golongan_id']}")

        komponen_data = all_komponen_gaji[all_komponen_gaji["profil_gaji_id"]
                                          == master_row["gaji_profil_id"]]
        komponen_df = pd.DataFrame(komponen_data).reset_index(drop=True)
        komponen_df["master_batch_id"] = master_row["id"]

        # Convert byte to bool for 'is_reference' field
        komponen_df["is_reference"] = komponen_df["is_reference"].apply(
            lambda value: bool(int.from_bytes(value, "little"))
        )

        # Set up nilai referensi komponen gaji
        log_debug("Setting up nilai referensi komponen gaji")
        start_time = datetime.datetime.now()
        komponen_df["nilai"] = komponen_df.apply(
            lambda row: row["nilai"] if not row["is_reference"] else setup_nilai_referensi_komponen_gaji(
                row, master_row, tunjangan_data, rumah_dinas_data, gaji_potongan_data,
                riwayat_sp_data, gaji_potongan_tkk_data, gaji_pendapatan_non_pajak_data),
            axis=1
        )
        log_debug(f"Finished setting up nilai referensi komponen gaji in {
            datetime.datetime.now() - start_time}")

        # Set up nilai formula
        log_debug("Setting up nilai formula")
        start_time = datetime.datetime.now()
        komponen_df.loc[:, "nilai_formula"] = komponen_df["formula"].apply(
            lambda x: replace_formula_to_variable(x)
        )
        komponen_df = calculate_nilai_formula(
            komponen_df, master_row, maksimal_potongan)
        log_debug(f"Finished setting up nilai formula in {
            datetime.datetime.now() - start_time}\n")

        komponen_df["nilai"] = komponen_df["nilai"].apply(
            lambda x: 0 if pd.isna(x) else x)

        # append komponen_df to result_komponen_list
        result_komponen_list = pd.concat([result_komponen_list, komponen_df])

    return gaji_batch_master_data, result_komponen_list


def setup_nilai_referensi_komponen_gaji(
        komponen: pd.Series,
        master_data: pd.DataFrame,
        tunjangan_data: pd.DataFrame,
        rumah_dinas_data: pd.DataFrame,
        gaji_potongan_tkk: pd.DataFrame,
        riwayat_sp_data: pd.DataFrame,
        gaji_potongan_tkk_data: pd.DataFrame,
        gaji_pendapatan_non_pajak_data: pd.DataFrame):
    match komponen["kode"]:
        case "GP":
            return master_data["gaji_pokok"]
        case "REF_TUNJ_JABATAN":
            nominal = filter_tunjangan_data(
                tunjangan_data,
                TUNJANGAN.JABATAN.value,
                master_data["level_id"],
                master_data["golongan_id"]
            )
            return 0 if nominal.empty else nominal["nominal"][0]
        case "REF_TUNJ_BERAS":
            nominal = filter_tunjangan_data(
                tunjangan_data,
                TUNJANGAN.BERAS.value,
                master_data["level_id"],
                master_data["golongan_id"]
            )
            return 0 if nominal.empty else nominal["nominal"][0]
        case "REF_TUNJ_KK":
            nominal = filter_tunjangan_data(
                tunjangan_data,
                TUNJANGAN.KINERJA.value,
                master_data["level_id"],
                master_data["golongan_id"]
            )
            return 0 if nominal.empty else nominal["nominal"][0]
        case "REF_TUNJ_AIR":
            nominal = filter_tunjangan_data(
                tunjangan_data,
                TUNJANGAN.AIR.value,
                master_data["level_id"],
                master_data["golongan_id"]
            )
            return 0 if nominal.empty else nominal["nominal"][0]
        case "REF_PHDP":
            return master_data["phdp"]
        case "REF_SEWA_RUMDIN":
            if pd.isna(master_data["rumah_dinas_id"]):
                return 0
            else:
                nominal = filter_rumah_dinas_by_id(
                    rumah_dinas_data,
                    int(master_data["rumah_dinas_id"])
                )
                return nominal["nilai"][0] if not nominal.empty else 0
        case "REF_POT_TKK":
            if gaji_potongan_tkk.empty:
                return 0

            nominal = filter_gaji_potongan_tkk(gaji_potongan_tkk, master_data["status_pegawai"],
                                               master_data["level_id"], master_data["golongan_id"])
            return 0 if nominal.empty else nominal["nominal"][0]
        case "REF_PTKP":
            nominal = filter_gaji_pendapatan_non_pajak(
                gaji_pendapatan_non_pajak_data, master_data["kode_pajak"])
            return 0 if nominal.empty else nominal["nominal"][0]
        case "REF_ASKES":
            return 1 if master_data["is_askes"] == True else 0
        case "REF_JML_POT_KK":
            return calculate_jml_pot_tkk(
                riwayat_sp_data,
                gaji_potongan_tkk_data,
                master_data["pegawai_id"],
                master_data["nipam"],
                master_data["status_pegawai"]
            )


def calculate_nilai_formula(komponen_gaji: pd.DataFrame, master_data: pd.DataFrame, maksimal_potongan: dict) -> pd.DataFrame:
    """
    Set up nilai formula for each komponen gaji.
    """
    for index, row in komponen_gaji.iterrows():
        # Create a dictionary of nilai komponen gaji
        komponen_gaji.sort_values(by="urut")
        nilai_komponen = {komponen["kode"]: komponen["nilai"]
                          for _, komponen in komponen_gaji.iterrows()}
        nilai_komponen["JML_ANAK"] = master_data["jml_tanggungan"]
        nilai_komponen["JML_JIWA"] = 1 + master_data["jml_tanggungan"] + \
            (0 if master_data["status_kawin"]
             != STATUS_KAWIN.KAWIN.value else 1)
        # set GP zero for TUNJ_SI and status_kawin not STATUS_KAWIN.KAWIN
        if row["kode"] == "TUNJ_SI" and master_data["status_kawin"] != STATUS_KAWIN.KAWIN.value:
            nilai_komponen["GP"] = 0

        # Replace variables in the formula with their values
        formula = row["nilai_formula"].strip()
        if formula in {"#SYSTEM", ""}:
            continue

        nilai_formula = replace_formula_with_values(
            formula, nilai_komponen)

        # Evaluate the formula
        try:
            nilai = round(safe_eval(nilai_formula), 2)
            if row["kode"] == "TUNJ_PPH21":
                nilai = 0 if nilai < 0 else nilai
            elif row["kode"] == "POT_JP" and nilai > maksimal_potongan["jpn"]:
                nilai = maksimal_potongan["jpn"]
            elif row["kode"] == "POT_ASKES" and nilai > maksimal_potongan["askes"]:
                nilai = maksimal_potongan["askes"]
        except Exception as error:
            ic(master_data["nipam"], master_data["nama"],
               row["kode"], row["formula"], nilai_formula)
            log_error(f"Error evaluating formula: {error}")

        # Update the nilai and nilai_formula columns in the komponen_gaji dataframe
        komponen_gaji.loc[index, "nilai_formula"] = nilai_formula
        komponen_gaji.loc[index, "nilai"] = nilai

    return komponen_gaji


def compare_with_latest_gaji(root_batch_id: str, master_data: pd.DataFrame):
    """
    Compare the current gaji with the latest gaji.
    """
    log_debug("Comparing with latest gaji")
    start_time = datetime.datetime.now()
    periode = root_batch_id.split("-")[0]
    periode_date = datetime.datetime.strptime(periode, "%Y%m").date()
    # minus 1 month
    prev_month = periode_date - datetime.timedelta(days=periode_date.day)
    prev_month = prev_month.strftime("%Y%m")
    latest_batch_master_data = pd.DataFrame(
        fetch_gaji_batch_master_by_periode(prev_month))
    if latest_batch_master_data.empty:
        log_debug("No latest gaji batch master data found\n")
        return

    different_gaji = []

    # comparing gaji pokok from 2 DataFrame between master_data with latest_batch_master_data if gaji pokok not equal then print gaji is changed
    for _, master_data in master_data.iterrows():
        for _, latest_gaji in latest_batch_master_data.iterrows():
            if master_data["pegawai_id"] == latest_gaji["pegawai_id"] and master_data["gaji_pokok"] != latest_gaji["gaji_pokok"]:
                different_gaji.append(
                    (master_data["root_batch_id"], master_data["pegawai_id"]))
    reset_different_gaji_batch_master_as_false(root_batch_id)
    if different_gaji:
        update_different_gaji_batch_master(different_gaji)

    log_debug(f"Comparing with latest gaji finished in {
              datetime.datetime.now() - start_time}")
