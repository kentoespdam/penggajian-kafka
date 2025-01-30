from core.config import log_info
from core.databases.gaji_batch_master import fetch_gaji_batch_master_data
from core.databases.gaji_komponen import fetch_gaji_komponen
from icecream import ic
import pandas as pd
import dask.dataframe as dd

from core.databases.gaji_batch_potongan_tkk import fetch_gaji_potongan_tkk_by_status_pegawai, get_jml_pot_tkk
from core.databases.gaji_pendapatan_non_pajak import fetch_gaji_pendaptan_non_pajak_by_kode_pajak
from core.databases.gaji_tunjangan import fetch_tunjangan_data
from core.databases.rumah_dinas import fetch_rumah_dinas_by_id
from core.enums import STATUS_KAWIN, STATUS_PEGAWAI, TUNJANGAN
from core.helper import replace_formula_with_values, safe_eval

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
    log_info(f"calculate gaji detail {root_batch_id}")
    gaji_batch_master_data = pd.DataFrame(
        fetch_gaji_batch_master_data(root_batch_id))

    if gaji_batch_master_data.empty:
        return False

    gaji_batch_master_data["is_askes"] = gaji_batch_master_data["is_askes"].apply(
        lambda x: False if x is None else bool(int.from_bytes(x, "little")))

    setup_gaji_komponen_detail(gaji_batch_master_data)

    return True


def setup_gaji_komponen_detail(gaji_batch_master_data: pd.DataFrame) -> None:
    """
    Set up gaji komponen detail for given gaji batch master data.

    Args:
        gaji_batch_master_data (pd.DataFrame): Gaji batch master data.
    """
    for _, master_row in gaji_batch_master_data.iterrows():
        komponen_data = fetch_gaji_komponen(master_row["gaji_profil_id"])
        komponen_df = pd.DataFrame(komponen_data).reset_index(drop=True)

        # Convert byte to bool
        komponen_df["is_reference"] = komponen_df["is_reference"].apply(
            lambda value: bool(int.from_bytes(value, "little"))
        )

        # Set up nilai referensi komponen gaji
        komponen_df["nilai"] = komponen_df.apply(
            lambda row: row["nilai"] if not row["is_reference"] else setup_nilai_referensi_komponen_gaji(
                row, master_row),
            axis=1
        )
        komponen_df["nilai_formula"] = komponen_df["formula"]
        komponen_df = setup_nilai_formula(komponen_df, master_row)

        ic(komponen_df.to_dict(orient="records"))


def setup_nilai_referensi_komponen_gaji(komponen: pd.Series, master_data: pd.DataFrame) -> float:
    match komponen["kode"]:
        case "GP":
            return master_data["gaji_pokok"]
        case "REF_TUNJ_JABATAN":
            return fetch_tunjangan_data(
                TUNJANGAN.JABATAN.value,
                master_data["level_id"],
                master_data["golongan_id"]
            ).get("nominal", 0)
        case "REF_TUNJ_BERAS":
            return fetch_tunjangan_data(
                TUNJANGAN.BERAS.value,
                master_data["level_id"],
                master_data["golongan_id"]
            ).get("nominal", 0)
        case "REF_TUNJ_KK":
            return fetch_tunjangan_data(
                TUNJANGAN.KINERJA.value,
                master_data["level_id"],
                master_data["golongan_id"]
            ).get("nominal", 0)
        case "REF_TUNJ_AIR":
            return fetch_tunjangan_data(
                TUNJANGAN.AIR.value,
                master_data["level_id"],
                master_data["golongan_id"]
            ).get("nominal", 0)
        case "REF_PHDP":
            return master_data["phdp"]
        case "REF_SEWA_RUMDIN":
            return 0 if not master_data["rumah_dinas_id"] else fetch_rumah_dinas_by_id(master_data["rumah_dinas_id"]).get("nominal", 0)
        case "REF_POT_TKK":
            return fetch_gaji_potongan_tkk_by_status_pegawai(
                master_data["status_pegawai"],
                master_data["level_id"],
                master_data["golongan_id"]
            ).get("nominal", 0)
        case "REF_PTKP":
            return fetch_gaji_pendaptan_non_pajak_by_kode_pajak(master_data["kode_pajak"]).get("nominal", 0)
        case "REF_ASKES":
            return master_data["is_askes"]
        case "REF_JML_POT_KK":
            return get_jml_pot_tkk(
                master_data["root_batch_id"],
                master_data["pegawai_id"],
                master_data["nipam"],
                master_data["status_pegawai"]
            )

    return 0


def setup_nilai_formula(komponen_gaji: pd.DataFrame, master_data: pd.DataFrame) -> pd.DataFrame:
    """
    Set up nilai formula for each komponen gaji.
    """
    for index, row in komponen_gaji.iterrows():
        # Create a dictionary of nilai komponen gaji
        nilai_komponen = {komponen["kode"]: komponen["nilai"]
                          for _, komponen in komponen_gaji.iterrows()}
        nilai_komponen["CEIL"] = "ceil"
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

        nilai_formula = replace_formula_with_values(formula, nilai_komponen)

        # Evaluate the formula
        try:
            nilai = round(safe_eval(nilai_formula), 2)
        except Exception as error:
            log_info(f"Error evaluating formula: {error}")

        # Update the nilai and nilai_formula columns in the komponen_gaji dataframe
        komponen_gaji.loc[index, "nilai_formula"] = nilai_formula
        komponen_gaji.loc[index, "nilai"] = nilai

    return komponen_gaji
