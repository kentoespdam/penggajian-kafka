from datetime import datetime
from pathlib import Path

import dask.dataframe as dd
import pandas as pd
from openpyxl import load_workbook

from core.config import LOGGER
from core.enums import STATUS_PEGAWAI
from core.helpers import cleanup_is_boolean, cleanup_empty_string
from core.models.gaji_batch_master import fetch_daftar_gaji_pegawai
from core.models.organisasi import fetch_organisasi_by_level
from core.process_gaji.phase3_generate_direksi import generate_direksi_sheet
from core.process_gaji.phase3_generate_hgpkp import generate_hgpkp_sheet
from core.process_gaji.phase3_generate_kontrak import generate_kontrak_sheet
from core.process_gaji.phase3_generate_pegawai import generate_pegawai_sheet

_raw_types = {
    "id": int,
    "nipam": str,
    "nama": str,
    "status_pegawai": int,
    "golongan": str,
    "pangkat": str,
    "jml_tanggungan": int,
    "jml_jiwa": int,
    "organisasi_id": int,
    "kode_organisasi": str,
    "nama_organisasi": str,
    "level_id": int,
    "is_different": str
}


def build_himpunan_gaji(batch_root_id: str) -> None:
    start_time = datetime.now()
    LOGGER.info("Starting phase3: build himpunan gaji for batch ID {}".format(batch_root_id))

    organisasi_df = fetch_organisasi_by_level(4)
    if organisasi_df.empty:
        LOGGER.error("Error Organisasi not found")
        return

    raw_datar_gaji_pegawai_df = fetch_daftar_gaji_pegawai(batch_root_id)
    if raw_datar_gaji_pegawai_df.empty:
        LOGGER.error("Error daftar gaji pegawai not found")
        return

    daftar_gaji_pegawai_df = raw_datar_gaji_pegawai_df[[
        "id", "nipam", "nama", "status_pegawai", "golongan", "pangkat", "jml_tanggungan",
        "jml_jiwa", "organisasi_id", "kode_organisasi", "nama_organisasi", "level_id", "is_different"
    ]].drop_duplicates(subset=["nipam"]).reset_index(drop=True)
    ddf = dd.from_pandas(daftar_gaji_pegawai_df, npartitions=2)
    ddf["golongan"] = ddf["golongan"].map(lambda x: cleanup_empty_string(x))
    ddf["pangkat"] = ddf["pangkat"].map(lambda x: cleanup_empty_string(x))
    ddf["is_different"] = ddf["is_different"].map(lambda x: cleanup_is_boolean(x), meta=("is_different", "object"))
    daftar_gaji_pegawai_df = ddf.compute()

    daftar_proses_gaji_df = raw_datar_gaji_pegawai_df[[
        "batch_master_id", "kode", "jenis_gaji", "nilai", "uraian", "kode_organisasi"
    ]].reset_index(drop=True)

    _generate_excel(batch_root_id, organisasi_df, daftar_gaji_pegawai_df, daftar_proses_gaji_df)

    end_time = datetime.now()
    LOGGER.info(f"build himpunan gaji finished in {end_time - start_time}")


def _generate_excel(
        batch_root_id: str,
        organisasi_df: pd.DataFrame,
        daftar_gaji_pegawai_df: pd.DataFrame,
        daftar_proses_gaji_df: pd.DataFrame
) -> None:
    periode = batch_root_id.split("-")[0]
    tahun = int(periode[0:4])
    bulan = int(periode[4:6])

    project_root = Path(__file__).parent.parent.parent
    wb = load_workbook(f"{project_root}/excel_template/daftar_gaji_template.xlsx")

    mask = daftar_gaji_pegawai_df["level_id"].isin([2, 3, 4])
    daftar_gaji_direksi_df = daftar_gaji_pegawai_df[mask].reset_index(drop=True)
    daftar_gaji_direksi_df.sort_values(by=["level_id"], inplace=True)
    daftar_gaji_direksi_df.reset_index(drop=True, inplace=True, col_level=0)

    mask = daftar_proses_gaji_df["batch_master_id"].isin(daftar_gaji_direksi_df["id"])
    daftar_proses_gaji_direksi_df = daftar_proses_gaji_df[mask].reset_index(drop=True)

    mask = daftar_gaji_pegawai_df["level_id"] == 4
    dirum = daftar_gaji_pegawai_df[mask].reset_index(drop=True)

    mask = daftar_gaji_pegawai_df["status_pegawai"] == STATUS_PEGAWAI.KONTRAK.value
    daftar_gaji_pegawai_kontrak_df=daftar_gaji_pegawai_df[mask].reset_index(drop=True)

    # generate sheet direksi
    # generate_direksi_sheet(wb, tahun, bulan, daftar_gaji_direksi_df, daftar_proses_gaji_direksi_df, dirum)
    # generate_pegawai_sheet(wb, organisasi_df, tahun, bulan, daftar_gaji_pegawai_df, daftar_proses_gaji_df, dirum)
    # generate_kontrak_sheet(wb, organisasi_df, tahun, bulan, daftar_gaji_pegawai_kontrak_df, daftar_proses_gaji_df, dirum)
    generate_hgpkp_sheet(wb, organisasi_df, tahun, bulan, daftar_gaji_pegawai_df, daftar_proses_gaji_df)

    wb.remove(wb["pegawai"])
    wb.remove(wb["kontrak"])
    wb.remove(wb["HGPKP1"])
    wb.remove(wb["HHTKKP1"])
    wb.remove(wb["HG1"])
    # wb.active = wb["HG"]
    wb.save(f"{project_root}/result_excel/daftar_gaji_{batch_root_id}.xlsx")
