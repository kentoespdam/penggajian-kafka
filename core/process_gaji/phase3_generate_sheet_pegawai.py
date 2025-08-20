import itertools

import pandas as pd
from openpyxl.worksheet.worksheet import Worksheet

from core.excel_helper import cell_builder
from core.process_gaji.phase3_generate_helper import generate_cell_list
from core.process_gaji.phase3_helper import (
    generate_ttd,
    total_columns,
    main_columns,
    get_sub_total_salary,
    get_sub_component_value,
)


def generate_sheet_per_organisasi(
    worksheet: Worksheet,
    pegawai_df: pd.DataFrame,
    komponen_gaji_df: pd.DataFrame,
    nama_organisasi: pd.Series,
    dirum: pd.DataFrame,
    year: int,
    month: int,
):
    row_num = itertools.count(start=12)
    order_num = itertools.count(start=1)
    for _, employee in pegawai_df.iterrows():
        next_row = _generate_organisasi_row(
            worksheet, next(row_num), next(order_num), employee, komponen_gaji_df
        )
        row_num = itertools.count(start=next_row)

    next_row = _generate_footer(
        worksheet, next(row_num), nama_organisasi, pegawai_df, komponen_gaji_df
    )
    row_num = itertools.count(start=next_row + 1)
    generate_ttd(worksheet, next(row_num), dirum, year, month)


def _generate_organisasi_row(
    worksheet: Worksheet,
    row_num: int,
    order_number: int,
    employee: pd.Series,
    komponen_gaji_df: pd.DataFrame,
):
    row_counter = itertools.count(start=row_num)
    column_index = itertools.count(start=1)

    def build_cell(
        value,
        horizontal_alignment=None,
        vertical_alignment=None,
    ) -> None:
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
    build_cell(
        employee["golongan"] if employee["golongan"] else "-",
        horizontal_alignment="center",
        vertical_alignment="center",
    )

    for index, column in enumerate(main_columns):
        current_row = next(row_counter)
        generate_cell_list(
            worksheet,
            current_row,
            5 if index == 0 else 1,
            komponen_gaji_df,
            employee,
            column,
            order_number=order_number,
            is_first=index == 0,
            is_last=index == 3,
        )

    return next(row_counter)


def _generate_footer(
    worksheet: Worksheet,
    row_num: int,
    nama_organisasi: pd.Series,
    pegawai_df: pd.DataFrame,
    komponen_gaji_df: pd.DataFrame,
):
    _generate_footer_title(worksheet, row_num, nama_organisasi, pegawai_df)
    row_counter = itertools.count(start=row_num)

    for index, column in enumerate(total_columns):
        current_row = next(row_counter)
        _generate_pegawai_footer_value(
            worksheet,
            current_row,
            column,
            komponen_gaji_df,
            is_first=index == 0,
            is_last=(index == 3),
        )

    return next(row_counter)


def _generate_footer_title(
    worksheet: Worksheet,
    row_num: int,
    nama_organisasi: pd.Series,
    pegawai_df: pd.DataFrame,
):
    total_pegawai = pegawai_df["id"].count()

    # Direksi Cell
    cell_builder(
        worksheet,
        row_num,
        1,
        f"Jumlah {nama_organisasi}",
        True,
        vertical_alignment="center",
        border={"top": "thin", "left": "thin", "right": "thin", "bottom": "thin"},
    )

    # Total Pegawai Cell
    cell_builder(
        worksheet,
        row_num,
        3,
        f"{total_pegawai} Pegawai",
        True,
        vertical_alignment="center",
        border={"top": "thin", "left": "thin", "right": "thin", "bottom": "thin"},
    )

    worksheet.merge_cells(
        start_row=row_num, start_column=1, end_column=2, end_row=row_num + 3
    )
    worksheet.merge_cells(
        start_row=row_num, start_column=3, end_column=4, end_row=row_num + 3
    )

    return row_num + 3


def _generate_pegawai_footer_value(
    worksheet: Worksheet,
    row_num: int,
    column_list: list,
    komponen_gaji_df: pd.DataFrame,
    is_first: bool = False,
    is_last: bool = False,
):
    col_num = itertools.count(start=5)

    def build_cell(content, is_number=False):
        cell = cell_builder(
            worksheet,
            row_num,
            next(col_num),
            content,
            border={
                "top": "thin" if is_first else None,
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if is_last else None,
            },
        )
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
