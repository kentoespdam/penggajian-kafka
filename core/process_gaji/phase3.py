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
from core.process_gaji.phase3_generate_hhtkkp import generate_hhtkkp_sheet
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

# Constants for selected columns
COLUMNS_GAJI_PEGAWAI = [
    "id",
    "nipam",
    "nama",
    "status_pegawai",
    "golongan",
    "pangkat",
    "jml_tanggungan",
    "jml_jiwa",
    "organisasi_id",
    "kode_organisasi",
    "nama_organisasi",
    "level_id",
    "is_different",
]

COLUMNS_PROSES_GAJI = [
    "batch_master_id",
    "kode",
    "jenis_gaji",
    "nilai",
    "uraian",
    "kode_organisasi",
]

# Constants
DIREKSI_LEVEL_IDS: tuple[int, ...] = (2, 3, 4)
DIRUM_LEVEL_ID: int = 4
TEMPLATE_REL_PATH = "excel_template/daftar_gaji_template.xlsx"
OUTPUT_REL_DIR = "result_excel"
SHEETS_TO_REMOVE: tuple[str, ...] = ("pegawai", "kontrak", "HGPKP1", "HHTKKP1", "HG1")


def build_himpunan_gaji(batch_root_id: str) -> None:
    """
    Build Himpunan Gaji (salary aggregation) and generate the Excel output for a given batch.
    """
    start_time = datetime.now()
    LOGGER.info(f"Starting phase3: build himpunan gaji for batch ID {batch_root_id}")

    organisasi_df = fetch_organisasi_by_level(4)
    if organisasi_df.empty:
        LOGGER.error("Organisasi not found")
        return

    raw_daftar_gaji_pegawai_df = fetch_daftar_gaji_pegawai(batch_root_id)
    if raw_daftar_gaji_pegawai_df.empty:
        LOGGER.error("Daftar gaji pegawai not found")
        return

    # Prepare pegawai dataframe
    pegawai_selected_df = _select_and_deduplicate_pegawai(raw_daftar_gaji_pegawai_df)
    daftar_gaji_pegawai_df = _clean_pegawai_df(pegawai_selected_df)

    # Prepare komponen gaji (proses) dataframe
    komponen_gaji_df = raw_daftar_gaji_pegawai_df[COLUMNS_PROSES_GAJI].reset_index(drop=True)

    _generate_excel(
        batch_root_id,
        organisasi_df,
        daftar_gaji_pegawai_df,
        komponen_gaji_df,
    )

    elapsed = datetime.now() - start_time
    LOGGER.info(f"Build himpunan gaji finished in {elapsed}")


def _generate_excel(
        batch_root_id: str,
        organisasi_df: pd.DataFrame,
        daftar_gaji_pegawai_df: pd.DataFrame,
        komponen_gaji_df: pd.DataFrame,
) -> None:
    year, month = _parse_year_month(batch_root_id)
    project_root = _get_project_root()
    wb = load_workbook(_get_template_path(project_root))

    # Direksi (levels 2, 3, 4)
    is_direksi = daftar_gaji_pegawai_df["level_id"].isin(DIREKSI_LEVEL_IDS)
    daftar_gaji_direksi_df = (
        daftar_gaji_pegawai_df.loc[is_direksi]
        .sort_values(by=["level_id"])
        .reset_index(drop=True)
    )

    proses_for_direksi = komponen_gaji_df["batch_master_id"].isin(daftar_gaji_direksi_df["id"])
    komponen_gaji_direksi_df = komponen_gaji_df.loc[proses_for_direksi].reset_index(drop=True)

    # DIRUM (level 4 only)
    is_dirum = daftar_gaji_pegawai_df["level_id"].eq(DIRUM_LEVEL_ID)
    dirum_df = daftar_gaji_pegawai_df.loc[is_dirum].reset_index(drop=True)

    # Pegawai Kontrak
    is_kontrak = daftar_gaji_pegawai_df["status_pegawai"].eq(STATUS_PEGAWAI.KONTRAK.value)
    daftar_gaji_pegawai_kontrak_df = daftar_gaji_pegawai_df.loc[is_kontrak].reset_index(drop=True)

    # Generate sheets
    # generate_direksi_sheet(wb, year, month, daftar_gaji_direksi_df, komponen_gaji_direksi_df, dirum_df)
    # generate_pegawai_sheet(wb, organisasi_df, year, month, daftar_gaji_pegawai_df, komponen_gaji_df, dirum_df)
    # generate_kontrak_sheet(wb, organisasi_df, year, month, daftar_gaji_pegawai_kontrak_df, komponen_gaji_df, dirum_df)
    # generate_hgpkp_sheet(wb, organisasi_df, year, month, daftar_gaji_pegawai_df, komponen_gaji_df)
    generate_hhtkkp_sheet(wb, organisasi_df, year, month, daftar_gaji_pegawai_df, komponen_gaji_df)

    # Cleanup template sheets and save
    _remove_template_sheets(wb)
    wb.save(_get_output_path(project_root, batch_root_id))


def _select_and_deduplicate_pegawai(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select the necessary columns for pegawai and deduplicate by NIPAM.
    """
    return (
        df[COLUMNS_GAJI_PEGAWAI]
        .drop_duplicates(subset=["nipam"])
        .reset_index(drop=True)
    )


def _clean_pegawai_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean specific pegawai columns using Dask for scalability.
    - Normalize golongan and pangkat empty strings
    - Normalize is_different to boolean-like value
    """
    ddf = dd.from_pandas(df, npartitions=2)
    ddf["golongan"] = ddf["golongan"].map(cleanup_empty_string)
    ddf["pangkat"] = ddf["pangkat"].map(cleanup_empty_string)
    ddf["is_different"] = ddf["is_different"].map(
        cleanup_is_boolean, meta=("is_different", "bool")
    )
    return ddf.compute()


def _parse_year_month(batch_root_id: str) -> tuple[int, int]:
    periode = batch_root_id.split("-")[0]
    return int(periode[0:4]), int(periode[4:6])


def _get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _get_template_path(project_root: Path) -> Path:
    return project_root / TEMPLATE_REL_PATH


def _get_output_path(project_root: Path, batch_root_id: str) -> Path:
    return project_root / OUTPUT_REL_DIR / f"daftar_gaji_{batch_root_id}.xlsx"


def _remove_template_sheets(wb) -> None:
    # Safely remove template sheets if present
    for name in SHEETS_TO_REMOVE:
        if name in wb.sheetnames:
            wb.remove(wb[name])
