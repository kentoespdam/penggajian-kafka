import itertools

import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.excel_helper import cell_builder
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_helper import get_total_salary, get_component_value, generate_footer_title, \
    get_sub_total_salary, get_sub_component_value, generate_ttd


def generate_direksi_sheet(
        workbook: Workbook,
        year: int,
        month: int,
        daftar_gaji_direksi_df: pd.DataFrame,
        daftar_proses_gaji_direksi_df: pd.DataFrame,
        dirum: pd.DataFrame
):
    workbook.active = workbook["pegawai"]
    active_sheet = workbook.active
    worksheet = workbook.copy_worksheet(active_sheet)
    worksheet.title = "DIREKSI"
    worksheet["A7"] = f"Bulan: {get_nama_bulan(month)} {year}"
    worksheet["A8"] = "DIREKSI"

    row_num = itertools.count(start=12)

    for index, row in daftar_gaji_direksi_df.iterrows():
        next_row = _generate_direksi_row(
            worksheet,
            next(row_num),
            index + 1,  # noqa
            row,
            daftar_proses_gaji_direksi_df
        )
        row_num = itertools.count(start=next_row)

    next_row = _generate_direksi_footer(
        worksheet,
        next(row_num),
        daftar_gaji_direksi_df,
        daftar_proses_gaji_direksi_df
    )
    row_num = itertools.count(start=next_row)

    generate_ttd(worksheet, next(row_num), dirum, year, month)


def _generate_direksi_row(
        worksheet: Worksheet,
        start_row: int,
        sequence_number: int,
        employee_data: pd.Series,
        salary_process_df: pd.DataFrame
):
    """Generate a row of cells for a single employee in the direksi sheet."""
    row_counter = itertools.count(start_row)
    column_counter = itertools.count(start=1)

    def build_cell(content: str | int | float | pd.Series, is_numeric: bool = False,
                   horizontal_alignment: str = None) -> None:
        """Build a single cell with the given content."""
        cell = cell_builder(
            worksheet,
            row_num=start_row,
            column_num=next(column_counter),
            content=content,
            border={"left": "thin", "right": "thin"},
            horizontal_alignment=horizontal_alignment
        )
        if is_numeric:
            cell.number_format = "#,##0"

    build_cell(sequence_number)
    build_cell(
        "{}{}".format(
            "** " if employee_data["is_different"] else "", employee_data["nama"]
        )
    )
    build_cell(employee_data["nipam"])
    build_cell("-", horizontal_alignment="center")

    # Create the columns for each component
    columns = [
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL"],
        ["", "", "", "JML_JIWA", "TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["", "", "", "", "TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["", "", "", "", "JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]

    for i, column in enumerate(columns):
        current_row = next(row_counter)
        _generate_cell_list(
            worksheet,
            current_row,
            5 if i == 0 else 1,
            employee_data,
            salary_process_df,
            column,
            sequence_number,
            is_first_row=(i == 0),
        )

    _generate_pemda_title(worksheet, next(row_counter), "Gaji yang telah diterima di PEMDA")

    pemda_values_components = [
        ["0", "0", "0", "0", "0", "0", "0", ""],
        ["0", "0", "0", "0", "0", "0", "", ""],
        ["0", "", "0", "0", "0", "0", "", ""],
        ["0", "", "0", "0", "0", "0", "", ""]
    ]

    for idx, component_list in enumerate(pemda_values_components):
        _generate_pemda_value(
            worksheet,
            next(row_counter) - 1,
            employee_data,
            salary_process_df,
            component_list,
            is_first=(idx == 0),
            is_last=(idx == len(pemda_values_components) - 1)
        )

    return next(row_counter) - 1


def _generate_cell_list(
        worksheet: Worksheet,
        row_num: int,
        start_column: int,
        employee_data: pd.Series,
        salary_process_df: pd.DataFrame,
        component_list: list[str],
        sequence_number: int | None = None,
        is_first_row: bool = False,
):
    """Generate a list of cells based on the given parameters."""
    column_index = itertools.count(start=start_column)

    def build_cell(content: str | int | float, is_numeric: bool = False, align: str | None = None) -> None:
        """Build a cell based on the given parameters."""
        cell = cell_builder(worksheet, row_num=row_num, column_num=next(column_index), content=content,
                            border={"left": "thin", "right": "thin"},
                            horizontal_alignment=align)
        if is_numeric:
            cell.number_format = "#,##0"

    for index, component in enumerate(component_list):
        if component == "0":
            build_cell(0, is_numeric=True)
        elif component == "":
            build_cell("")
        elif component == "JUMLAH":
            build_cell(
                get_total_salary(salary_process_df, employee_data["id"]),
                is_numeric=True
            )
        elif component == "JML_JIWA":
            build_cell(
                f"{employee_data['jml_tanggungan']} / {employee_data['jml_jiwa']}",
                align="center"
            )
        else:
            build_cell(
                get_component_value(salary_process_df, employee_data["id"], component),
                is_numeric=True
            )

    if is_first_row:
        build_cell(str(sequence_number))


def _generate_pemda_title(worksheet: Worksheet, row_num: int, value: str):
    column_index = itertools.count(start=1)

    # Build the first cell without content
    cell_builder(worksheet, row_num, next(column_index), "", border={"left": "thin", "right": "thin"})

    # Build the merged cell with bold font
    cell_builder(
        worksheet,
        row_num,
        next(column_index),
        value,
        font_bold=True,
        border={
            "top": "thin",
            "left": "thin",
            "right": "thin",
            "bottom": "thin"
        },
        vertical_alignment="top",
        horizontal_alignment="center"
    )
    worksheet.merge_cells(start_row=row_num, start_column=2, end_row=row_num + 3, end_column=4)


def _generate_pemda_value(
        worksheet: Worksheet,
        row_num: int,
        employee_data: pd.Series,
        salary_process_df: pd.DataFrame,
        component_list: list[str],
        is_first: bool = False,
        is_last: bool = False
):
    col_num = itertools.count(start=5)
    is_last_component = False

    if is_last:
        cell_builder(
            worksheet,
            row_num,
            1,
            "",
            border={
                "left": "thin",
                "right": "thin",
                "bottom": "thin"
            }
        )

    def build_cell(value: str | int | float, is_number: bool = False):
        cell = cell_builder(
            worksheet,
            row_num,
            next(col_num),
            value,
            horizontal_alignment="right",
            border={
                "top": "thin" if is_first and not is_last_component else None,
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if is_last else None
            }
        )
        if is_number:
            cell.number_format = "#,##0"

    for index, component in enumerate(component_list):
        if index == len(component_list) - 1:
            is_last_component = True
        if component == "0":
            build_cell(0, is_number=True)
        elif component == "":
            build_cell("")
        elif component == "JUMLAH":
            build_cell(get_total_salary(salary_process_df, employee_data["id"]), True)
        else:
            build_cell(get_component_value(salary_process_df, employee_data["id"], component), True)

    return row_num + 1


def _generate_direksi_footer(
        worksheet: Worksheet,
        row_num: int,
        daftar_gaji_direksi_df: pd.DataFrame,
        daftar_proses_gaji_direksi_df: pd.DataFrame
):
    generate_footer_title(worksheet, row_num, daftar_gaji_direksi_df)
    row_counter = itertools.count(start=row_num)

    for index, component_list in enumerate([
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN",
         "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""],
        ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR",
         "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]):
        current_row = next(row_counter)
        _generate_footer_values(worksheet, current_row, daftar_proses_gaji_direksi_df, component_list,
                                is_end=index == 3)

    next(row_counter)
    return next(row_counter)


def _generate_footer_values(
        worksheet: Worksheet,
        row_num: int,
        daftar_gaji_direksi_df: pd.DataFrame,
        component_list: list[str],
        is_end: bool = False,
):
    """Generate footer values for Direksi template."""
    col_num = itertools.count(start=5)

    def build_cell(value: str | int | float, is_number: bool = False) -> None:
        cell = cell_builder(
            worksheet=worksheet,
            row_num=row_num,
            column_num=next(col_num),
            content=value,
            border={
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if is_end else None
            }
        )
        if is_number:
            cell.number_format = "#,##0"

    for component in component_list:
        if component == "0":
            build_cell(0, True)
        elif component == "":
            build_cell("")
        elif component == "JUMLAH":
            build_cell(get_sub_total_salary(daftar_gaji_direksi_df), True)
        else:
            build_cell(get_sub_component_value(daftar_gaji_direksi_df, component), True)

