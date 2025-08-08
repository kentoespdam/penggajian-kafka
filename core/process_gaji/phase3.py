import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from core.config import LOGGER
from core.models.gaji_batch_master import fetch_daftar_potongan_gaji_by_batch_root_id
from core.models.organisasi import fetch_organisasi_by_level
from core.process_gaji.phase3_generate import generate_potongan


def build_himpunan_gaji(batch_root_id: str) -> None:
    start_time = datetime.now()
    LOGGER.info("Starting phase3: build himpunan gaji for batch ID {}".format(batch_root_id))

    organisasi_df = fetch_organisasi_by_level(4)
    if organisasi_df.empty:
        LOGGER.error("Error Organisasi not found")
        return

    daftar_potongan_gaji_df = fetch_daftar_potongan_gaji_by_batch_root_id(batch_root_id)
    if daftar_potongan_gaji_df.empty:
        LOGGER.error("Error daftar potongan gaji not found")
        return

    generate_excel(batch_root_id, organisasi_df, daftar_potongan_gaji_df)

    end_time = datetime.now()
    LOGGER.info(f"process gaji finished in {end_time - start_time}")


def generate_excel(batch_root_id: str, organisasi_df: pd.DataFrame,
                   daftar_potongan_gaji_df: pd.DataFrame):
    periode = batch_root_id.split("-")[0]
    tahun = int(periode[0:4])
    bulan = int(periode[4:6])
    project_root = Path(__file__).parent.parent.parent

    wb = load_workbook(f"{project_root}/excel_template/potongan_gaji_template.xlsx")

    potongan_gaji_direksi_df = daftar_potongan_gaji_df[
        daftar_potongan_gaji_df["level_id"].isin([2, 3, 4])
    ].reset_index(drop=True)

    # generate sheet direksi
    generate_potongan(wb, "DIREKSI", "DIREKSI", tahun, bulan, potongan_gaji_direksi_df)

    for _, organisasi in organisasi_df.iterrows():
        mask = daftar_potongan_gaji_df["kode_organisasi"].str.startswith(f"{organisasi['kode']}")
        potongan_gaji_pegawai = daftar_potongan_gaji_df[mask].reset_index(drop=True)
        generate_potongan(wb, f"{organisasi['nama']}", f"{organisasi['short_name']}", tahun, bulan,
                          potongan_gaji_pegawai)

    wb.remove(wb["Sheet1"])
    wb.save(f"{project_root}/result_excel/potongan_gaji_{batch_root_id}.xlsx")
