import itertools

import pandas as pd
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from core.excel_helper import cell_builder
from core.helpers import get_nama_bulan

main_columns = [
    ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL"],
    ["", "", "", "", "TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
    ["", "", "", "", "TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
    ["", "", "", "", "JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
]

total_columns = [
    ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""],
    ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
    ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
    ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
]


def get_total_salary(salary_process_df: pd.DataFrame, employee_id: pd.Series) -> float:
    """Get the total salary of an employee based on the given parameters."""
    base_salary = get_component_value(salary_process_df, employee_id, "GP")
    si_allowance = get_component_value(salary_process_df, employee_id, "TUNJ_SI")
    child_allowance = get_component_value(salary_process_df, employee_id, "TUNJ_ANAK")
    return base_salary + si_allowance + child_allowance


def get_sub_total_salary(salary_process_df: pd.DataFrame) -> float:
    """Get the total salary of an employee based on the given parameters."""
    base_salary = get_sub_component_value(salary_process_df, "GP")
    si_allowance = get_sub_component_value(salary_process_df, "TUNJ_SI")
    child_allowance = get_sub_component_value(salary_process_df, "TUNJ_ANAK")
    return base_salary + si_allowance + child_allowance


def get_component_value(salary_process_df: pd.DataFrame, batch_master_id: pd.Series, component: str) -> float:
    """Get the value of a component based on the given parameters."""
    mask = (salary_process_df["batch_master_id"] == batch_master_id) & (salary_process_df["kode"] == component)
    row = salary_process_df[mask]
    return row["nilai"].values[0] if not row.empty else 0


def get_sub_component_value(salary_process_df: pd.DataFrame, component: str) -> float:
    """Get the value of a component based on the given parameters."""
    mask = salary_process_df["kode"] == component
    row = salary_process_df[mask]
    return row["nilai"].sum() if not row.empty else 0


def generate_footer_title(worksheet: Worksheet, row_num: int, row_data: pd.DataFrame) -> int:
    total_pegawai = row_data["id"].count()
    dir_column = cell_builder(worksheet=worksheet, row_num=row_num, column_num=1, content="DIREKSI",
                              border={"top": "thin", "bottom": "thin", "left": "thin", "right": "thin"},
                              horizontal_alignment="center", vertical_alignment="center")
    dir_column.font = Font(bold=True)
    worksheet.merge_cells(start_row=row_num, start_column=1,
                          end_column=2, end_row=row_num + 3)
    jml_column = cell_builder(worksheet=worksheet, row_num=row_num, column_num=3, content=f"{total_pegawai} Pegawai",
                              border={"top": "thin", "bottom": "thin", "left": "thin", "right": "thin"},
                              horizontal_alignment="center", vertical_alignment="center")
    jml_column.font = Font(bold=True)
    worksheet.merge_cells(start_row=row_num, start_column=3,
                          end_column=4, end_row=row_num + 3)
    return row_num + 3


def generate_ttd(
        worksheet: Worksheet,
        row_num: int,
        employee_data: pd.DataFrame,
        year: int,
        month: int
):
    row_index = itertools.count(start=row_num)

    def build_cell(value: str | int | float) -> None:
        row = next(row_index)
        cell_builder(
            worksheet=worksheet,
            row_num=row,
            column_num=10,
            content=value,
            horizontal_alignment="center",
        )
        worksheet.merge_cells(start_row=row, start_column=10, end_row=row, end_column=11)

    build_cell(f"Purwokerto,        {get_nama_bulan(month)} {year}")
    build_cell("DIREKSI PERUMDAM TIRTA SATRIA")
    build_cell("KABUPATEN BANYUMAS")
    build_cell("Direktur Umum")
    for _ in range(3): next(row_index)
    build_cell(employee_data["nama"].values[0])
    build_cell(f"NIPAM. {employee_data['nipam'].values[0]}")
