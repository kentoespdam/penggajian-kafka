import itertools
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.config import LOGGER
from core.excel_helper import cell_builder
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_helper import get_total_salary, get_component_value, generate_footer_title, \
    get_sub_total_salary, get_sub_component_value, generate_ttd


@dataclass
class PositionTracker:
    row: int
    order: int

    def next_row(self) -> int:
        current = self.row
        self.row += 1
        return current

    def next_order(self) -> int:
        current = self.order
        self.order += 1
        return current

    def advance_rows(self, steps: int = 1) -> None:
        self.row += steps


def generate_direksi_sheet(
        workbook: Workbook,
        year: int,
        month: int,
        daftar_gaji_direksi_df: pd.DataFrame,
        daftar_proses_gaji_direksi_df: pd.DataFrame,
        dirum: pd.DataFrame
):
    start_time = datetime.now()
    LOGGER.info(f"Starting phase3: Generate direksi sheet for year {year} and month {month}")

    workbook.active = workbook["pegawai"]
    active_sheet = workbook.active
    worksheet = workbook.copy_worksheet(active_sheet)
    worksheet.title = "DIREKSI"
    worksheet["A7"] = f"Bulan: {get_nama_bulan(month)} {year}"
    worksheet["A8"] = "DIREKSI"

    tracker = PositionTracker(row=12, order=1)

    for index, row in daftar_gaji_direksi_df.iterrows():
        _generate_direksi_row(
            worksheet,
            tracker,
            row,
            daftar_proses_gaji_direksi_df
        )

    _generate_direksi_footer(
        worksheet,
        tracker,
        daftar_gaji_direksi_df,
        daftar_proses_gaji_direksi_df
    )

    tracker.next_row()
    generate_ttd(worksheet, tracker.next_row(), dirum, year, month)

    elapsed = datetime.now() - start_time
    LOGGER.info(f"Generate direksi sheet finished in {elapsed}")


def _generate_direksi_row(
        worksheet: Worksheet,
        pos: PositionTracker,
        employee_data: pd.Series,
        salary_process_df: pd.DataFrame
):
    """Generate a row of cells for a single employee in the direksi sheet."""
    column_counter = itertools.count(start=1)

    def build_cell(content: str | int | float | pd.Series, row_num: int, is_numeric: bool = False,
                   horizontal_alignment: str = None) -> None:
        """Build a single cell with the given content."""
        cell = cell_builder(
            worksheet,
            row_num,
            column_num=next(column_counter),
            content=content,
            border={"top": "thin", "left": "thin", "right": "thin"},
            horizontal_alignment=horizontal_alignment
        )
        if is_numeric:
            cell.number_format = "#,##0"

    current_row = pos.next_row()
    current_order = pos.next_order()
    build_cell(current_order, current_row)
    build_cell(
        "{}{}".format(
            "** " if employee_data["is_different"] else "", employee_data["nama"]
        ),
        current_row
    )
    build_cell(employee_data["nipam"], current_row)
    build_cell("-", current_row, horizontal_alignment="center")

    first_cells = ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL"]
    _generate_cell_list(
        worksheet,
        current_row,
        5,
        employee_data,
        salary_process_df,
        first_cells,
        current_order,
        is_first_row=True
    )

    # Create the columns for each component
    columns = [
        ["", "", "", "JML_JIWA", "TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["", "", "", "", "TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["", "", "", "", "JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]

    for i, column in enumerate(columns):
        _generate_cell_list(
            worksheet,
            pos.next_row(),
            1,
            employee_data,
            salary_process_df,
            column,
        )

    current_row = pos.next_row()
    _generate_pemda_title(worksheet, current_row, "Gaji yang telah diterima di PEMDA")
    first_cells = ["0", "0", "0", "0", "0", "0", "0", ""]
    _generate_cell_list(
        worksheet,
        current_row,
        5,
        employee_data,
        salary_process_df,
        first_cells,
        is_first_row=True,
        is_title=True
    )

    pemda_values_components = [
        ["0", "0", "0", "0", "0", "0", "", ""],
        ["0", "", "0", "0", "0", "0", "", ""],
        ["0", "", "0", "0", "0", "0", "", ""]
    ]

    for idx, component_list in enumerate(pemda_values_components):
        _generate_pemda_value(
            worksheet,
            pos.next_row(),
            employee_data,
            salary_process_df,
            component_list
        )

    current_row = pos.next_row()
    _generate_pemda_title(worksheet, current_row, "Kekurangan yang harus dibayar PDAM")

    first_cells = ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""]
    _generate_cell_list(
        worksheet,
        current_row,
        5,
        employee_data,
        salary_process_df,
        first_cells,
        is_first_row=True,
        is_title=True
    )

    columns = [
        ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]
    for i, column in enumerate(columns):
        _generate_cell_list(
            worksheet,
            pos.next_row(),
            5,
            employee_data,
            salary_process_df,
            column,
        )


def _generate_cell_list(
        worksheet: Worksheet,
        row_num: int | str,
        start_column: int,
        employee_data: pd.Series,
        salary_process_df: pd.DataFrame,
        component_list: list[str],
        sequence_number: int | None = None,
        is_first_row: bool = False,
        is_title: bool = False,
):
    """Generate a list of cells based on the given parameters."""
    column_index = itertools.count(start=start_column)
    is_border_top = is_first_row

    def build_cell(content: str | int | float, is_numeric: bool = False, align: str | None = None) -> None:
        """Build a cell based on the given parameters."""
        cell = cell_builder(worksheet, row_num=row_num, column_num=next(column_index), content=content,
                            border={"top": "thin" if is_border_top else None, "left": "thin", "right": "thin"},
                            horizontal_alignment=align)
        if is_numeric:
            cell.number_format = "#,##0"

    for index, component in enumerate(component_list):
        # is_border_top = False
        if is_title and index == len(component_list) - 1:
            is_border_top = False
        if component == "0":
            build_cell(0, is_numeric=True)
        elif component == "":
            build_cell("")
        elif component == "JUMLAH":
            build_cell(get_total_salary(salary_process_df, employee_data["id"]), is_numeric=True)
        elif component == "JML_JIWA":
            build_cell(f"{employee_data['jml_tanggungan']} / {employee_data['jml_jiwa']}", align="center")
        else:
            build_cell(get_component_value(salary_process_df, employee_data["id"], component), is_numeric=True)

    if is_first_row and sequence_number is not None:
        build_cell(sequence_number)


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
        border={"top": "thin", "left": "thin", "right": "thin", "bottom": "thin"},
        vertical_alignment="top",
    )
    worksheet.merge_cells(start_row=row_num, start_column=2, end_row=row_num + 3, end_column=4)


def _generate_pemda_value(
        worksheet: Worksheet,
        row_num: int,
        employee_data: pd.Series,
        salary_process_df: pd.DataFrame,
        component_list: list[str],
):
    col_num = itertools.count(start=5)

    def build_cell(value: str | int | float, is_number: bool = False):
        cell = cell_builder(
            worksheet,
            row_num,
            next(col_num),
            value,
            horizontal_alignment="right",
            border={"left": "thin", "right": "thin", }
        )
        if is_number:
            cell.number_format = "#,##0"

    for index, component in enumerate(component_list):
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
        pos: PositionTracker,
        daftar_gaji_direksi_df: pd.DataFrame,
        daftar_proses_gaji_direksi_df: pd.DataFrame
):
    current_row = pos.next_row()
    generate_footer_title(worksheet, current_row, daftar_gaji_direksi_df)
    first_column = ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""]
    _generate_footer_values(worksheet, current_row, daftar_proses_gaji_direksi_df, first_column, True)

    for index, component_list in enumerate([
        ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]):
        _generate_footer_values(worksheet, pos.next_row(), daftar_proses_gaji_direksi_df, component_list,
                                border_bottom=index == 2)


def _generate_footer_values(
        worksheet: Worksheet,
        row_num: int,
        daftar_gaji_direksi_df: pd.DataFrame,
        component_list: list[str],
        border_top: bool = False,
        border_bottom: bool = False,
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
                "top": "thin" if border_top else None,
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if border_bottom else None
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
