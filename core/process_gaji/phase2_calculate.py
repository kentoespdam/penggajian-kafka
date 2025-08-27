import pandas as pd

from core.config import LOGGER
from core.enums import StatusKawin, Tunjangan
from core.helpers import safe_eval
from core.process_gaji.phase2_helper import replace_formula_with_values, _filter_tunjangan, _filter_rumah_dinas, \
    _filter_potongan_tkk, _filter_pendapatan_non_pajak, _filter_jml_potongan_tkk, filter_komponen_by_kode


def _setup_nilai_referensi_komponen_gaji(
        kode: str,
        master_row: pd.Series,
        tunjangan_df: pd.DataFrame,
        rumah_dinas_df: pd.DataFrame,
        potongan_tkk_df: pd.DataFrame,
        gaji_batch_potongan_tkk_df: pd.DataFrame,
        gaji_pendapatan_non_pajak_df: pd.DataFrame
):
    """
    Set up nilai referensi komponen gaji given kode, master_row, and relevant dataframes.

    Args:
        kode (str): Kode of the komponen gaji.
        master_row (pd.Series): Row of the master table.
        tunjangan_df (pd.DataFrame): Dataframe of tunjangan.
        rumah_dinas_df (pd.DataFrame): Dataframe of rumah_dinas.
        potongan_tkk_df (pd.DataFrame): Dataframe of potongan_tkk.
        gaji_batch_potongan_tkk_df (pd.DataFrame): Dataframe of gaji_batch_potongan_tkk.
        gaji_pendapatan_non_pajak_df (pd.DataFrame): Dataframe of gaji_pendapatan_non_pajak.

    Returns:
        int or float: Nilai referensi of the komponen gaji.

    Notes:
        - This is a helper function to set up nilai referensi komponen gaji given kode, master_row, and relevant dataframes.
        - It uses the `match-case` statement to determine which type of nilai referensi to return based on the kode.
        - The function also logs the result of the calculation for each type of nilai referensi.
    """
    level_id = master_row["level_id"]
    golongan_id = master_row["golongan_id"]
    match kode:
        case "GP":
            # Gaji Pokok
            result = master_row["gaji_pokok"]
            LOGGER.debug(f"Gaji Pokok: {result}")
            return result
        case "REF_TUNJ_JABATAN":
            # Tunjangan Jabatan
            result = _filter_tunjangan(
                tunjangan_df,
                Tunjangan.JABATAN.value,
                level_id,  # noqa
                golongan_id,  # noqa
            )
            LOGGER.debug(f"Tunjangan Jabatan: {result}")
            return result
        case "REF_TUNJ_BERAS":
            # Tunjangan Beras
            return _filter_tunjangan(
                tunjangan_df,
                Tunjangan.BERAS.value,
                7,  # noqa
                golongan_id,  # noqa
            )
        case "REF_TUNJ_KK":
            # Tunjangan Kinerja
            result = _filter_tunjangan(
                tunjangan_df,
                Tunjangan.KINERJA.value,
                level_id,  # noqa
                golongan_id,  # noqa
            )
            LOGGER.debug(f"Tunjangan Kinerja: {result}")
            return result
        case "REF_TUNJ_AIR":
            # Tunjangan Air
            result = _filter_tunjangan(
                tunjangan_df,
                Tunjangan.AIR.value,
                level_id,  # noqa
                golongan_id,  # noqa
            )
            LOGGER.debug(f"Tunjangan Air: {result}")
            return result
        case "REF_PHDP":
            # PHDP
            result = master_row["phdp"]
            LOGGER.debug(f"PHDP: {result}")
            return result
        case "REF_SEWA_RUMDIN":
            # Sewa Rumah Dinas
            result = 0 if master_row["rumah_dinas_id"] == 0 else _filter_rumah_dinas(
                rumah_dinas_df,
                master_row["rumah_dinas_id"]  # noqa
            )
            LOGGER.debug(f"Sewa Rumah Dinas: {result}")
            return result
        case "REF_POT_TKK":
            # Potongan TKK
            result = 0 if gaji_batch_potongan_tkk_df.empty else _filter_potongan_tkk(
                potongan_tkk_df,
                master_row["status_pegawai"],  # noqa
                master_row["level_id"],  # noqa
                master_row["golongan_id"],  # noqa
            )
            LOGGER.debug(f"Potongan TKK: {result}")
            return result
        case "REF_PTKP":
            # Pendapatan Non Pajak
            result = _filter_pendapatan_non_pajak(
                gaji_pendapatan_non_pajak_df,
                master_row["kode_pajak"]  # noqa
            )
            LOGGER.debug(f"Pendapatan Non Pajak: {result}")
            return result
        case "REF_ASKES":
            # ASKES
            result = 1 if master_row["is_askes"] else 0
            LOGGER.debug(f"ASKES: {result}")
            return result
        case "REF_JML_POT_TKK":
            # Jumlah Potongan TKK
            result = _filter_jml_potongan_tkk(
                gaji_batch_potongan_tkk_df,
                master_row["nipam"],  # noqa
            )
            LOGGER.debug(f"Jumlah Potongan TKK: {result}")
            return result
        case _:
            # Default value
            return 0


def _cleanup_nilai_referensi_komponen_gaji(
        df: pd.Series,
        master_row: pd.Series,
        tunjangan_df: pd.DataFrame,
        rumah_dinas_df: pd.DataFrame,
        potongan_tkk_df: pd.DataFrame,
        gaji_batch_potongan_tkk_df: pd.DataFrame,
        gaji_pendapatan_non_pajak_df: pd.DataFrame
) -> pd.Series:
    """
    Clean up nilai referensi komponen gaji with actual values from respective dataframes.

    Parameters
    ----------
    df : pd.Series of nilai referensi komponen gaji
    master_row : pd.Series of master data row
    tunjangan_df : pd.DataFrame of tunjangan
    rumah_dinas_df : pd.DataFrame of rumah dinas
    potongan_tkk_df : pd.DataFrame of potongan TKK
    gaji_batch_potongan_tkk_df : pd.DataFrame of potongan TKK for this batch
    gaji_pendapatan_non_pajak_df : pd.DataFrame of pendapatan non pajak

    Returns
    -------
    pd.Series of nilai referensi komponen gaji with actual values
    """
    return df.apply(
        lambda x: x if pd.isna(x) else _setup_nilai_referensi_komponen_gaji(
            x, master_row, tunjangan_df,
            rumah_dinas_df, potongan_tkk_df,
            gaji_batch_potongan_tkk_df,
            gaji_pendapatan_non_pajak_df
        ),
        meta=("nilai", "float64")
    )


def _calculate_nilai_formula(
        komponen_gaji_df: pd.DataFrame,
        master_row: pd.Series,
        maksimal_potongan: dict,
) -> pd.DataFrame:
    """
    Calculate nilai komponen gaji based on its formula.

    Parameters
    ----------
    komponen_gaji_df : pd.DataFrame of komponen gaji
    master_row : pd.Series
        Series of master_data row
    maksimal_potongan : dict
        Dictionary of maximum potongan values

    Returns
    -------
    pd.DataFrame of komponen gaji with calculated nilai
    """
    for index, row in komponen_gaji_df.iterrows():
        nilai_komponen = {str(komponen["kode"]): komponen["nilai"] for _, komponen in
                          komponen_gaji_df.iterrows()}
        nilai_komponen["JML_ANAK"] = master_row["jml_tanggungan"]
        nilai_komponen["JML_JIWA"] = 1 + master_row["jml_tanggungan"] + (
            0 if master_row["status_kawin"] != StatusKawin.KAWIN.value else 1)

        if row["kode"] == "TUNJ_SI" and master_row["status_kawin"] != StatusKawin.KAWIN.value:
            nilai_komponen["GP"] = 0

        formula = row["nilai_formula"].strip()
        if formula in {"#SYSTEM", ""}:
            continue

        nilai_formula = replace_formula_with_values(
            formula, nilai_komponen)

        try:
            nilai = round(safe_eval(nilai_formula))
        except Exception as error:
            LOGGER.error(
                f"Error evaluating formula: {error} for {master_row['nipam']} {master_row['nama']} {row['kode']} {row['formula']} {nilai_formula}")
            continue

        if row["kode"] == "TUNJ_PPH21" and nilai < 0:
            nilai = 0
        elif row["kode"] == "POT_JP" and nilai > maksimal_potongan["jpn"]:
            nilai = maksimal_potongan["jpn"]
        elif row["kode"] == "POT_ASKES" and nilai > maksimal_potongan["askes"]:
            nilai = maksimal_potongan["askes"]

        komponen_gaji_df.at[index, "nilai"] = nilai
        komponen_gaji_df.at[index, "nilai_formula"] = nilai_formula

    return komponen_gaji_df


def _applying_dataframe(df: pd.DataFrame, mbp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply mapping of columns to master batch process dataframe values.

    Parameters
    ----------
    df : pd.DataFrame to apply mapping to
    mbp_df : pd.DataFrame of master batch process

    Returns
    -------
    pd.DataFrame with applied mapping
    """
    # Define a mapping of dataframe columns to their corresponding codes
    columns_mapping = {
        "penghasilan_kotor": "PENGHASILAN_KOTOR",
        "total_potongan": "POTONGAN",
        "penghasilan_bersih": "PENGHASILAN_BERSIH",
        "pembulatan": "PEMBULATAN",
        "penghasilan_bersih_final": "PENGHASILAN_BERSIH_FINAL",
        "pajak": "POT_PPH21",
    }

    # Apply the mapping to each row in the dataframe
    for col, kode in columns_mapping.items():
        # For each column, update its values based on the corresponding 'kode'
        df.loc[:, col] = df["id"].apply(
            lambda x: round(filter_komponen_by_kode(x, mbp_df, kode))
            if col == "pajak"
            else filter_komponen_by_kode(x, mbp_df, kode))

    return df
