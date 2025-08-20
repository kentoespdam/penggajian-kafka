import itertools
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.config import LOGGER
from core.excel_helper import cell_builder
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_helper import get_component_value, get_sub_component_value, generate_ttd


def generate_kontrak_sheet(
        workbook: Workbook,
        organisasi_df: pd.DataFrame,
        year: int,
        month: int,
        daftar_gaji_pegawai_df: pd.DataFrame,
        daftar_proses_gaji_pegawai_df: pd.DataFrame,
        dirum: pd.DataFrame
):
    start_time = datetime.now()
    LOGGER.info(f"Starting phase3: Generate kontrak per organisasi sheet for year {year} and month {month}")

    if daftar_gaji_pegawai_df.empty:
        elapsed = datetime.now() - start_time
        LOGGER.info(f"Generate kontrak sheet finished in {elapsed}")
        return

    list_organisasi_id = daftar_gaji_pegawai_df["organisasi_id"].unique().tolist()
    mask = organisasi_df["id"].isin(list_organisasi_id)
    organisasi_df = organisasi_df[mask].reset_index(drop=True)

    workbook.active = workbook["kontrak"]
    worksheet = workbook.active

    for _, organisasi in organisasi_df.iterrows():
        current_sheet = workbook.copy_worksheet(worksheet)
        current_sheet.title = f"KONTRAK-{organisasi['short_name']}"
        current_sheet["A7"] = f"Bulan: {get_nama_bulan(month)} {year}"
        current_sheet["A8"] = f"{organisasi['nama']}"

        mask_pegawai = (daftar_gaji_pegawai_df["kode_organisasi"].str.startswith(f"{organisasi['kode']}"))
        pegawai_df = daftar_gaji_pegawai_df[mask_pegawai].reset_index(drop=True)
        pegawai_df.sort_values(by=["level_id", "golongan"], ascending=[True, False], inplace=True)
        pegawai_df.reset_index(drop=True, inplace=True, col_level=0)

        pegawai_id_list = pegawai_df["id"].tolist()
        mask_proses = daftar_proses_gaji_pegawai_df["batch_master_id"].isin(pegawai_id_list)
        komponen_gaji_df = daftar_proses_gaji_pegawai_df[mask_proses].reset_index(drop=True)

        _generate_sheet_per_organisasi(current_sheet, pegawai_df, komponen_gaji_df, dirum, year, month)
        LOGGER.info(f"organisasi: {organisasi['short_name']}")

    elapsed = datetime.now() - start_time
    LOGGER.info(f"Generate kontrak sheet finished in {elapsed}")


def _generate_sheet_per_organisasi(
        worksheet: Worksheet,
        employees_df: pd.DataFrame,
        salary_components_df: pd.DataFrame,
        dirum: pd.DataFrame,
        year: int,
        month: int
):
    row_num = itertools.count(start=12)
    for index, employee in employees_df.iterrows():
        current_row_num = next(row_num)
        col_num = itertools.count(1)
        cell_builder(
            worksheet,
            current_row_num,
            next(col_num),
            index + 1,  # noqa
            border={"left": "thin", "right": "thin", "bottom": "thin"})
        cell_builder(worksheet,
                     current_row_num,
                     next(col_num),
                     f"{'** ' if employee['is_different'] else ''}{employee['nama']}",
                     border={"left": "thin", "right": "thin", "bottom": "thin"})
        net_col_num = _generate_organisasi_row(
            worksheet, current_row_num, next(col_num), employee, salary_components_df
        )
        col_num = itertools.count(start=net_col_num)
        cell_builder(
            worksheet,
            current_row_num,
            next(col_num),
            index + 1,  # noqa
            horizontal_alignment="left",
            border={"left": "thin", "right": "thin", "bottom": "thin"})

    _generate_footer(worksheet, next(row_num), salary_components_df)
    next(row_num)
    generate_ttd(worksheet, next(row_num), dirum, year, month)


def _generate_organisasi_row(
        worksheet: Worksheet,
        row_num: int,
        col_num: int,
        employee: pd.Series,
        salary_components_df: pd.DataFrame
):
    col_num = itertools.count(col_num)

    def build_cell(value: str | float, is_number: bool = False):
        cell = cell_builder(worksheet, row_num, next(col_num), value,
                            border={"left": "thin", "right": "thin", "bottom": "thin"})
        if is_number:
            cell.number_format = "#,##0"

    for komponen in ["GP", "POT_ASTEK", "POT_JP", "POT_ASKES", 0, "POTONGAN", "PEMBULATAN", "PENGHASILAN_BERSIH_FINAL"]:
        build_cell(get_component_value(salary_components_df, employee["id"], komponen), True)
    return next(col_num)


def _generate_footer(worksheet: Worksheet, row_num: int, salary_components_df: pd.DataFrame):
    col_num = itertools.count(1)

    def build_cell(value: str | float, is_number: bool = False, font_bold: bool = False, h_align: str = None):
        cell = cell_builder(worksheet, row_num, next(col_num), value, font_bold, horizontal_alignment=h_align,
                            border={"left": "thin", "right": "thin", "bottom": "thin"})
        if is_number:
            cell.number_format = "#,##0"

        return cell

    build_cell("JUMLAH", font_bold=True, h_align="center")
    worksheet.merge_cells(start_row=row_num, start_column=1,
                          end_column=next(col_num), end_row=row_num)
    for komponen in ["GP", "POT_ASTEK", "POT_JP", "POT_ASKES", 0, "POTONGAN", "PEMBULATAN", "PENGHASILAN_BERSIH_FINAL"]:
        build_cell(get_sub_component_value(salary_components_df, komponen), True)
    build_cell("")
