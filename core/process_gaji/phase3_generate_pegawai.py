import pandas as pd
from openpyxl import Workbook

from core.config import LOGGER
from core.enums import STATUS_PEGAWAI
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_generate_sheet_pegawai import generate_sheet_per_organisasi


def generate_pegawai_sheet(
        workbook: Workbook,
        organisasi_df: pd.DataFrame,
        year: int,
        month: int,
        daftar_gaji_pegawai_df: pd.DataFrame,
        daftar_proses_gaji_pegawai_df: pd.DataFrame,
        dirum: pd.DataFrame
):
    workbook.active = workbook["pegawai"]
    worksheet = workbook.active

    for _, organisasi in organisasi_df.iterrows():
        current_sheet = workbook.copy_worksheet(worksheet)
        current_sheet.title = organisasi["short_name"]
        current_sheet["A7"] = f"Bulan: {get_nama_bulan(month)} {year}"
        current_sheet["A8"] = f"{organisasi['nama']}"

        mask_pegawai = (daftar_gaji_pegawai_df["kode_organisasi"].str.startswith(f"{organisasi['kode']}")) & (
                daftar_gaji_pegawai_df["status_pegawai"] != STATUS_PEGAWAI.KONTRAK.value)
        pegawai_df = daftar_gaji_pegawai_df[mask_pegawai].reset_index(drop=True)
        pegawai_df.sort_values(by=["level_id", "golongan"], ascending=[True, False], inplace=True)

        pegawai_id_list = pegawai_df["id"].tolist()
        mask_proses = daftar_proses_gaji_pegawai_df["batch_master_id"].isin(pegawai_id_list)
        komponen_gaji_df = daftar_proses_gaji_pegawai_df[mask_proses].reset_index(drop=True)

        generate_sheet_per_organisasi(current_sheet, pegawai_df, komponen_gaji_df, organisasi["nama"], dirum, year,
                                      month)
        LOGGER.info(f"organisasi: {organisasi['short_name']}")
