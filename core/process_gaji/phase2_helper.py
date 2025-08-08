import pandas as pd

from core.config import LOGGER


def _cleanup_is_boolean(x):
    x.encode("utf-8")
    return True if x == '\x01' else False


def _filter_tunjangan(tunjangan_df: pd.DataFrame, tunjangan_type: int, level_id: int, golongan_id: int) -> float:
    if level_id in {5, 6}:
        condition = "(jenis_tunjangan == @tunjangan_type) & (level_id == @level_id)"
    else:
        condition = "(jenis_tunjangan == @tunjangan_type) & (golongan_id == @golongan_id)"

    filtered_df = tunjangan_df.query(condition).reset_index(drop=True)

    return filtered_df["nominal"].values[0] if not filtered_df.empty else 0


def _filter_rumah_dinas(rumah_dinas_df: pd.DataFrame, rumah_dinas_id: int) -> float:
    filtered_df = rumah_dinas_df.query("id == @rumah_dinas_id").reset_index(drop=True)

    return filtered_df["nilai"].values[0] if not filtered_df.empty else 0


def _filter_potongan_tkk(gaji_batch_potongan_tkk_df: pd.DataFrame, status_pegawai: int, level_id: int,
                         golongan_id: int) -> float:
    filtered_df = gaji_batch_potongan_tkk_df.query(
        "(status_pegawai == @status_pegawai) & (level_id == @level_id) & (golongan_id == @golongan_id)"
    ).reset_index(drop=True)

    return filtered_df["nominal"].values[0] if not filtered_df.empty else 0


def _filter_pendapatan_non_pajak(gaji_pendapatan_non_pajak_df: pd.DataFrame, kode_pajak: str) -> float:
    filtered_df = gaji_pendapatan_non_pajak_df.query("kode == @kode_pajak").reset_index(drop=True)

    return filtered_df["nominal"].values[0] if not filtered_df.empty else 0


def _filter_jml_potongan_tkk(potongan_tkk_df: pd.DataFrame, nipam: str) -> float:
    filtered_df = potongan_tkk_df.query("nipam == @nipam").reset_index(drop=True)

    return filtered_df["potongan"].values[0] if not filtered_df.empty else 0


def _replace_formula_to_variable(formula: str) -> str:
    tokens = formula.split(" ")
    for i, token in enumerate(tokens):
        token = token.strip().replace(",", ".")
        if token in {"+", "-", "*", "/", "%", "^", "(", ")", "CEIL", "CEIL(", "#SYSTEM", ""}:
            continue
        # Check if the token is a number
        elif not token.replace('.', '', 1).isdigit():
            # If not a number, format as a variable
            tokens[i] = "{" + token + "}"
    result = " ".join(tokens).replace("CEIL", "ceil").replace(",", ".")
    return result


def replace_formula_with_values(formula: str, lookup: dict) -> str:
    try:
        formated = formula.format(**lookup)
    except Exception as error:
        LOGGER.error(f"Error evaluating formula: {error}")
        LOGGER.error(lookup)
        return ""
    return formated


def filter_komponen_by_kode(batch_master_id: str, komponen_df: pd.DataFrame, kode: str) -> float:
    """
    Filter komponen by kode and sum nilai

    Args:
        batch_master_id (str): The batch master id
        komponen_df (pd.DataFrame): The dataframe containing the komponen records
        kode (str): The kode to filter by

    Returns:
        float: The sum of the nilai from the filtered records
    """
    filtered_df = komponen_df.query("(batch_master_id == @batch_master_id) and (kode == @kode)").reset_index(drop=True)
    # Return the sum of the nilai if the dataframe is not empty
    # Otherwise return 0
    return filtered_df["nilai"].sum() if not filtered_df.empty else 0
