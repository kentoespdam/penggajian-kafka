import pandas as pd

from core.enums import StatusPegawai
from core.process_gaji.phase3_helper import DIREKSI_LEVEL_IDS

# Domain constants
CABANG_PREFIX: str = "CABANG"


def filter_organisasi(organisasi_df: pd.DataFrame, is_cabang: bool = False) -> pd.DataFrame:
    """
    Select only non-branch (non-CABANG) organizations.
    """
    mask = organisasi_df["nama"].str.startswith(CABANG_PREFIX)
    return organisasi_df.loc[mask if is_cabang else ~mask].reset_index(drop=True)


def filter_gaji_direksi(gaji_pegawai_df: pd.DataFrame) -> pd.DataFrame:
    """
    Select employees whose level_id is in DIREKSI_LEVEL_IDS, sorted by level_id.
    """
    is_direksi = gaji_pegawai_df["level_id"].isin(DIREKSI_LEVEL_IDS)
    return (
        gaji_pegawai_df.loc[is_direksi]
        .sort_values(by=["level_id"])
        .reset_index(drop=True)
    )


def filter_gaji_pegawai(organisasi_df: pd.DataFrame, gaji_pegawai_df: pd.DataFrame) -> pd.DataFrame:
    """
    Select employees whose 'kode_organisasi' starts with any of the provided organisasi 'kode' values.
    """
    kode_prefixes = tuple(organisasi_df["kode"].tolist())
    mask_organisasi = gaji_pegawai_df["kode_organisasi"].str.startswith(kode_prefixes)
    mask_pegawai = gaji_pegawai_df["status_pegawai"].ne(StatusPegawai.KONTRAK.value)
    mask = mask_organisasi & mask_pegawai
    return gaji_pegawai_df.loc[mask].reset_index(drop=True)


def filter_komponen_by_batch_ids(komponen_gaji_df: pd.DataFrame, batch_ids: pd.Series) -> pd.DataFrame:
    """
    Filter komponen_gaji rows by a collection of batch_master_id values.
    """
    mask = komponen_gaji_df["batch_master_id"].isin(batch_ids)
    return komponen_gaji_df.loc[mask].reset_index(drop=True)


def filter_gaji_kontrak(gaji_pegawai_df: pd.DataFrame) -> pd.DataFrame:
    """
    Select only contract employees based on StatusPegawai.KONTRAK.
    """
    is_kontrak = gaji_pegawai_df["status_pegawai"].eq(StatusPegawai.KONTRAK.value)
    return gaji_pegawai_df.loc[is_kontrak].reset_index(drop=True)


def filter_gaji_komponen_by_kode(komponen_gaji_df: pd.DataFrame, kode: str) -> pd.DataFrame:
    mask = komponen_gaji_df["kode"].eq(kode)
    return komponen_gaji_df.loc[mask].reset_index(drop=True)


def get_nilai_by_cabang(komponen_gaji_df: pd.DataFrame, cabang_kode: str = None) -> float:
    if cabang_kode is None:
        return komponen_gaji_df["nilai"].sum()
    mask = komponen_gaji_df["kode_organisasi"].str.startswith(cabang_kode)
    return komponen_gaji_df.loc[mask]["nilai"].sum()
