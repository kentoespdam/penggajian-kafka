# Python
import itertools
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.config import LOGGER
from core.excel_helper import cell_builder, NUMBER_FORMAT, copy_sheet_from_template
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_helper import get_sub_component_value, filter_kontrak_pegawai

# Constants
_TEMPLATE_SHEET_NAME = "HHTKKP1"
_OUTPUT_SHEET_NAME = "HHTKKP"
_HEADER_ROW = 7
_DATA_START_ROW = 12
_COMPONENTS_ORDER = [
    "GP",
    "POT_ASTEK",
    "POT_JP",
    "POT_ASKES",
    0,  # numeric zero column
    "POTONGAN",
    "PENGHASILAN_BERSIH_FINAL",
    "",  # trailing empty column
]


def generate_hhtkkp_sheet(
        workbook: Workbook,
        organisasi_df: pd.DataFrame,
        year: int,
        month: int,
        gaji_pegawai_df: pd.DataFrame,
        komponen_gaji_df: pd.DataFrame
) -> None:
    """
    Generate HHTKKP sheet (Himpunan Honor Tenaga Kontrak Kantor Pusat).
    Steps:
    - Copy the template sheet and set the period header
    - Select non-branch organizations (non-CABANG)
    - Select contract employees and normalize their organization codes
    - Align organizations and employees by normalized codes
    - Filter salary components for the selected contract employees
    - Write per-organization rows and a final total row
    """
    start_time = datetime.now()
    LOGGER.info("Starting phase3: build HHTKKP (Himpunan Honor Tenaga Kontrak Kantor Pusat)")

    # Prepare worksheet from template
    worksheet = copy_sheet_from_template(workbook, _TEMPLATE_SHEET_NAME, _OUTPUT_SHEET_NAME)
    worksheet.cell(row=_HEADER_ROW, column=1, value=f"Bulan: {get_nama_bulan(month)} {year}")

    # Filter non-branch organizations
    pusat_org_df = _filter_non_cabang(organisasi_df)

    # Filter contract employees and normalize their org codes to align with organisasi codes
    kontrak_df = filter_kontrak_pegawai(gaji_pegawai_df).copy()
    kontrak_df.loc[:, "kode_organisasi"] = _normalize_kode_organisasi(kontrak_df["kode_organisasi"])

    # Keep only organizations referenced by contract employees
    kontrak_org_codes = kontrak_df["kode_organisasi"].unique().tolist()
    in_kontrak_orgs = pusat_org_df["kode"].isin(kontrak_org_codes)
    pusat_org_df = pusat_org_df.loc[in_kontrak_orgs].reset_index(drop=True)

    # Keep only contract employees that belong to the selected non-branch organizations
    selected_org_codes = set(pusat_org_df["kode"].tolist())
    in_selected_orgs = kontrak_df["kode_organisasi"].isin(selected_org_codes)
    kontrak_pusat_df = kontrak_df.loc[in_selected_orgs].reset_index(drop=True)

    # Filter komponen gaji for the selected employees
    selected_components_df = _filter_components_by_batch_ids(
        komponen_gaji_df, kontrak_pusat_df["id"]
    )

    row_counter = itertools.count(start=_DATA_START_ROW)
    urut_counter = itertools.count(start=1)

    for organisasi in pusat_org_df.itertuples():
        pegawai_mask = kontrak_pusat_df["kode_organisasi"].str.startswith(f"{organisasi.kode}")
        kontrak_pegawai_org_df = kontrak_pusat_df[pegawai_mask].reset_index(drop=True)
        kontrak_id_list = kontrak_pegawai_org_df["id"].to_list()

        org_components_df = selected_components_df[
            selected_components_df["batch_master_id"].isin(kontrak_id_list)
        ].reset_index(drop=True)

        _write_hhtkkp_row(
            worksheet=worksheet,
            row_number=next(row_counter),
            components_df=org_components_df,
            org_name=organisasi.nama,
            order_no=next(urut_counter),
        )

    # Final total row
    _write_hhtkkp_row(worksheet, next(row_counter), selected_components_df, "JUMLAH")

    elapsed = datetime.now() - start_time
    LOGGER.info(f"Finished building HHTKKP in {elapsed}")


def _filter_non_cabang(organisasi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only non-branch (non-CABANG) organizations.
    """
    is_non_branch = ~organisasi_df["nama"].str.startswith("CABANG")
    return organisasi_df.loc[is_non_branch].reset_index(drop=True)


def _normalize_kode_organisasi(kode_series: pd.Series) -> pd.Series:
    """
    Normalize organization code length:
    - If length is 5, keep the first 3 characters
    - Otherwise keep the first 5 characters
    """
    return kode_series.apply(lambda x: x[:3] if len(x) == 5 else x[:5])


def _filter_components_by_batch_ids(komponen_gaji_df: pd.DataFrame, batch_ids: pd.Series) -> pd.DataFrame:
    """
    Filter komponen_gaji rows that belong to the given batch_master_id list/series.
    """
    belongs = komponen_gaji_df["batch_master_id"].isin(batch_ids)
    return komponen_gaji_df.loc[belongs].reset_index(drop=True)


def _write_hhtkkp_row(
        worksheet: Worksheet,
        row_number: int,
        components_df: pd.DataFrame,
        org_name: str,
        order_no: int | None = None,
) -> None:
    """
    Write a single summarized HHTKKP row for an organization or the final total row.
    """
    column_counter = itertools.count(start=1)
    is_bold = False

    def build_cell(value, is_number: bool = False, h_align: str | None = None, v_align: str | None = None):
        cell = cell_builder(
            worksheet=worksheet,
            row_num=row_number,
            column_num=next(column_counter),
            content=value,
            font_bold=is_bold,
            horizontal_alignment=h_align,
            vertical_alignment=v_align,
            border={"left": "thin", "right": "thin", "bottom": "thin"},
        )
        if is_number:
            cell.number_format = NUMBER_FORMAT

    if order_no is not None and org_name != "JUMLAH":
        is_bold = False
        build_cell(order_no, True)
        build_cell(org_name)
    else:
        is_bold = True
        build_cell(org_name, h_align="center")
        next(column_counter)  # skip one column
        worksheet.merge_cells(start_row=row_number, start_column=1, end_row=row_number, end_column=2)

    for component in _COMPONENTS_ORDER:
        if component == "":
            build_cell("")
        elif component == 0:
            build_cell(0, True)
        else:
            build_cell(get_sub_component_value(components_df, component), True)
