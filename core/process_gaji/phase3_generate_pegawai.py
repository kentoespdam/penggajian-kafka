import itertools

import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.enums import STATUS_PEGAWAI
from core.excel_helper import cell_builder
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_helper import get_total_salary, get_component_value, get_sub_total_salary, \
    get_sub_component_value
from phase3_helper import generate_ttd

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

        pegawai_id_list = pegawai_df["id"].tolist()
        mask_proses = daftar_proses_gaji_pegawai_df["batch_master_id"].isin(pegawai_id_list)
        komponen_gaji_df = daftar_proses_gaji_pegawai_df[mask_proses].reset_index(drop=True)

        _generate_sheet_per_organisasi(current_sheet, pegawai_df, komponen_gaji_df, dirum, year, month)


def _generate_sheet_per_organisasi(worksheet: Worksheet, pegawai_df: pd.DataFrame, komponen_gaji_df: pd.DataFrame,
                                   dirum: pd.DataFrame, year: int, month: int):
    row_num = itertools.count(start=12)
    order_num = itertools.count(start=1)
    for _, employee in pegawai_df.iterrows():
        next_row = _generate_organisasi_row(
            worksheet, next(row_num), next(order_num), employee, komponen_gaji_df
        )
        row_num = itertools.count(start=next_row)

    next_row = _generate_footer(worksheet, next(row_num), pegawai_df, komponen_gaji_df)
    row_num = itertools.count(start=next_row)
    generate_ttd(worksheet, next(row_num), dirum, year, month)


def _generate_organisasi_row(worksheet: Worksheet, row_num: int, order_number: int, employee: pd.Series,
                             komponen_gaji_df: pd.DataFrame):
    row_counter = itertools.count(start=row_num)
    column_index = itertools.count(start=1)

    def build_cell(value: str | int | float, horizontal_alignment: str = None,
                   vertical_alignment: str = None) -> None:
        cell_builder(
            worksheet=worksheet,
            row_num=row_num,
            column_num=next(column_index),
            content=value,
            horizontal_alignment=horizontal_alignment,
            vertical_alignment=vertical_alignment,
            border={"left": "thin", "right": "thin"},
        )

    build_cell(order_number)
    build_cell(f"{'** ' if employee['is_different'] else ''}{employee['nama']}")
    build_cell(f"{employee['nipam']}")
    build_cell(employee["golongan"] if employee["golongan"]
               else "-", horizontal_alignment="center", vertical_alignment="center")

    columns = [
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL"],
        ["", "", "", "", "TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["", "", "", "", "TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["", "", "", "", "JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]

    for index, column in enumerate(columns):
        current_row = next(row_counter)
        _generate_cell_list(worksheet, current_row, 5 if index == 0 else 1,
                            komponen_gaji_df, employee, column, order_number=order_number, is_first=index == 0,
                            is_last=index == 3)

    next_row = next(row_counter)
    return next_row


def _generate_cell_list(worksheet: Worksheet, row_num: int, col_num: int, komponen_gaji_df: pd.DataFrame,
                        employee: pd.Series, komponen_list: list, order_number: int, is_first: bool = False,
                        is_last: bool = False):
    col_num = itertools.count(start=col_num)

    def build_cell(value: str | int | float, is_number: bool = False):
        cell = cell_builder(worksheet, row_num, next(col_num), value,
                            border={"left": "thin", "right": "thin", "bottom": "thin" if is_last else None})
        if is_number:
            cell.number_format = "#,##0"

    for komponen in komponen_list:
        if komponen == "0":
            build_cell(0, True)
        elif komponen == "":
            build_cell("")
        elif komponen == "JUMLAH":
            build_cell(get_total_salary(komponen_gaji_df, employee["id"]), True)
        else:
            build_cell(get_component_value(komponen_gaji_df, employee["id"], komponen), True)

    if is_first:
        build_cell(str(order_number))


def _generate_footer(worksheet: Worksheet, row_num: int, pegawai_df: pd.DataFrame, komponen_gaji_df: pd.DataFrame):
    _generate_footer_title(worksheet, row_num, pegawai_df)
    row_counter = itertools.count(start=row_num)

    columns = [
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""],
        ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]

    for index, column in enumerate(columns):
        current_row = next(row_counter)
        _generate_pegawai_footer_value(worksheet, current_row, column, komponen_gaji_df, is_last=(index == 3))

    return next(row_counter)


def _generate_footer_title(worksheet: Worksheet, row_num: int, pegawai_df: pd.Series):
    total_pegawai = pegawai_df["id"].count()

    # Direksi Cell
    cell_builder(worksheet, row_num, 1, "DIREKSI", font_bold=True, vertical_alignment="center",
                 border={"top": "thin", "left": "thin", "right": "thin", "bottom": "thin"})
    worksheet.merge_cells(start_row=row_num, start_column=1, end_row=row_num + 3, end_column=2)

    # Total Pegawai Cell
    cell_builder(worksheet, row_num, 3, f"{total_pegawai} Pegawai", True,
                 vertical_alignment="center",
                 border={"top": "thin", "left": "thin", "right": "thin", "bottom": "thin"})
    worksheet.merge_cells(start_row=row_num, start_column=3, end_row=row_num + 3, end_column=4)

    return row_num + 3


def _generate_pegawai_footer_value(worksheet: Worksheet, row_num: int, column_list: list,
                                   komponen_gaji_df: pd.DataFrame,
                                   is_last: bool = False):
    col_num = itertools.count(start=1)

    def build_cell(content, is_number=False):
        cell = cell_builder(worksheet, row_num, next(col_num), content,
                            border={"left": "thin", "right": "thin", "bottom": "thin" if is_last else None})
        if is_number:
            cell.number_format = "#,##0"

    for column in column_list:
        if column == "0":
            build_cell(0, True)
        elif column == "":
            build_cell("")
        elif column == "JUMLAH":
            build_cell(get_sub_total_salary(komponen_gaji_df), True)
        else:
            build_cell(get_sub_component_value(komponen_gaji_df, column), True)
