import itertools
from datetime import datetime

import pandas as pd
from openpyxl.styles import Alignment, Font
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.config import LOGGER
from core.enums import STATUS_PEGAWAI
from core.excel_helper import cell_builder, NUMBER_FORMAT
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_helper import get_sub_total_salary, get_sub_component_value


def generate_hgpkp_sheet(
        workbook: Workbook,
        organisasi_df: pd.DataFrame,
        year: int,
        month: int,
        gaji_pegawai_df: pd.DataFrame,
        komponen_gaji_df: pd.DataFrame,
) -> None:
    """
    Generate a sheet for HGPKP.

    Args:
    ----------
        workbook : Workbook where the sheet will be generated.
        organisasi_df : pd.DataFrame containing the list of organisasi.
        year : int The year of the report.
        month : int The month of the report.
        gaji_pegawai_df : pd.DataFrame containing the list of pegawai.
        komponen_gaji_df : pd.DataFrame containing the list of komponen gaji for each pegawai.
    """
    start_time = datetime.now()
    LOGGER.info(f"Starting phase3: Generate HGPKP sheet for year {year} and month {month}")

    workbook.active = workbook["HGPKP1"]
    worksheet = workbook.copy_worksheet(workbook.active)
    worksheet.title = "HGPKP"
    worksheet.cell(row=7, column=2, value=f"Bulan: {get_nama_bulan(month)} {year}")

    row_counter = itertools.count(start=16)
    order_counter = itertools.count(start=2)

    # Generate rows for direksi
    direksi_mask = gaji_pegawai_df["level_id"].isin([2, 3, 4])
    direksi_ids = gaji_pegawai_df[direksi_mask]["id"].tolist()

    komponen_gaji_direksi = komponen_gaji_df[komponen_gaji_df["batch_master_id"].isin(direksi_ids)].reset_index(
        drop=True)

    next_row = _generate_row(
        worksheet,
        next(row_counter),
        komponen_gaji_direksi,
        len(direksi_ids),
        "DIREKSI",
        next(order_counter),
    )
    row_counter = itertools.count(next_row)

    # Generate rows for organisasi
    non_cabang_mask = ~organisasi_df["nama"].str.startswith("CABANG")
    organisasi_pusat_df = organisasi_df[non_cabang_mask].reset_index(drop=True)

    for _, organisasi in organisasi_pusat_df.iterrows():
        organisasi_mask = gaji_pegawai_df["kode_organisasi"].str.startswith(f"{organisasi['kode']}")
        pegawai_mask = gaji_pegawai_df["status_pegawai"] != STATUS_PEGAWAI.KONTRAK.value
        mask = organisasi_mask & pegawai_mask
        pegawai_ids = tuple(gaji_pegawai_df[mask]["id"].to_list())

        mask = komponen_gaji_df["batch_master_id"].isin(pegawai_ids)
        komponen_gaji_organisasi = komponen_gaji_df[mask].reset_index(drop=True)

        next_row = _generate_row(
            worksheet,
            next(row_counter),
            komponen_gaji_organisasi,
            len(pegawai_ids),
            f"{organisasi['nama']}",
            next(order_counter)
        )
        row_counter = itertools.count(start=next_row)

    # Generate footer
    non_kontrak_mask = gaji_pegawai_df["status_pegawai"] != STATUS_PEGAWAI.KONTRAK.value
    mask_organisasi_codes = tuple(organisasi_pusat_df["kode"].unique().tolist())
    pegawai_mask = non_kontrak_mask & (
            gaji_pegawai_df["kode_organisasi"].str.startswith(mask_organisasi_codes) |
            gaji_pegawai_df["level_id"].isin([2, 3, 4])
    )
    all_pegawai_ids = gaji_pegawai_df[pegawai_mask]["id"].tolist()

    komponen_gaji_pegawai = komponen_gaji_df[komponen_gaji_df["batch_master_id"].isin(all_pegawai_ids)].reset_index(
        drop=True)

    next_row = _generate_row(
        worksheet,
        next(row_counter),
        komponen_gaji_pegawai,
        len(all_pegawai_ids),
        row_name="Total Sampai Halaman Ini"
    )
    worksheet.merge_cells(start_row=next_row - 5, start_column=1, end_column=2, end_row=next_row - 1)
    total_cell = worksheet.cell(row=next_row - 5, column=1)
    total_cell.alignment = Alignment(horizontal="center", vertical="center")
    total_cell.font = Font(bold=True)
    jml_cell = worksheet.cell(row=next_row - 5, column=1)
    jml_cell.alignment = Alignment(horizontal="center", vertical="center")
    jml_cell.font = Font(bold=True)

    elapsed_time = datetime.now() - start_time
    LOGGER.info(f"Finished phase3: Generate HGPKP sheet for year {year} and month {month} in {elapsed_time}")

def _generate_row(
        worksheet: Worksheet,
        start_row: int,
        salary_components: pd.DataFrame,
        pegawai_count: int,
        row_name: str,
        urut: int | None = None,
) -> int:
    """
    Generates rows in a worksheet for salary components and employee data.

    This function takes a worksheet object, starting row index, DataFrame of salary components,
    count of employees, a row name, and optional order number. It creates and formats
    cells in the worksheet to represent the salary information and alignment based on
    provided data. It processes specific salary component structures to update rows
    and columns accordingly.

    Args:
        worksheet: Worksheet object where rows will be created and populated with data
        start_row: Row index in the worksheet to start generating rows
        salary_components: DataFrame containing salary component data for employees
        pegawai_count: Number of employees to include in the data row
        row_name: Name to be displayed in row heading
        urut: Optional order number for the row
    :return: The next row index after rows have been generated and populated
    """
    column_index = itertools.count(start=1)

    def build_cell(value: str | int | float, is_number: bool = False, h_align: str | None = None) -> None:
        """
        Builds a cell in the worksheet with given content and formatting.

        :param value: Value to be displayed in the cell
        :param is_number: True if the cell should be formatted as a number
        :param h_align: Horizontal alignment of the cell
        """
        cell = cell_builder(
            worksheet=worksheet,
            row_num=start_row,
            column_num=next(column_index),
            content=value,
            horizontal_alignment=h_align,
            border={"left": "thin", "right": "thin"},
        )
        if is_number:
            cell.number_format = "#,##0"

    if urut is not None:
        # If the order number is present, use it as the first column
        build_cell(urut, True)
        build_cell(row_name)
    else:
        # If the order number is not present, use the row name as the first column
        build_cell(row_name)
        next(column_index)
    build_cell(pegawai_count, h_align="center")

    row_counter = itertools.count(start=start_row)
    columns = [
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN", "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""],
        ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR", "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["", "", "", "", "POT_JP", "", "", ""],
        ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "0", "POTONGAN", "", ""],
    ]

    # Iterate over the columns and generate cell lists
    for index, component_list in enumerate(columns):
        current_row = next(row_counter)
        generate_cell_list(
            worksheet,
            current_row,
            salary_components,
            component_list,
            index == 0,
            index == 4,
        )

    return next(row_counter)


def generate_cell_list(
        worksheet: Worksheet,
        row_num: int,
        salary_components_df: pd.DataFrame,
        components: list[str],
        is_first_row: bool = False,
        is_last_row: bool = False,
) -> None:
    """
    Generate a list of cells in a worksheet at a specific row, formatting their content
    and styles based on various conditions.

    Args:
        worksheet: The worksheet object where the cells will be added.
        row_num: The row number in the worksheet where cells will be created.
        salary_components_df: A DataFrame containing salary component data used for calculations.
        components: A list of salary components to be represented as cells.
        is_first_row: Specifies if the row is the first row in a group, altering the start column number. Defaults to False.
        is_last_row: Specifies if the row is the last row in a group, altering bottom border styling. Defaults to False.
    """
    start_column = 4 if is_first_row else 1
    column_counter = itertools.count(start=start_column)
    top_border = False

    def build_cell(value: str | float, is_number: bool = False) -> None:
        cell = cell_builder(
            worksheet=worksheet,
            row_num=row_num,
            column_num=next(column_counter),
            content=value,
            border={
                "top": "thin" if top_border else None,
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if is_last_row else None,
            },
        )
        if is_number:
            cell.number_format = "#,##0"

    if not is_first_row:
        for _ in range(3):
            build_cell("")

    for component in components:
        top_border = False
        if component == "POTONGAN":
            top_border = True
        if component == "0":
            build_cell(0, True)
        elif component == "":
            build_cell("")
        elif component == "JUMLAH":
            build_cell(get_sub_total_salary(salary_components_df), True)
        else:
            build_cell(
                get_sub_component_value(salary_components_df, component), True
            )


def _generate_footer(worksheet: Worksheet, row_num: int) -> None:
    """
    Generate and format the footer section at the given row in the worksheet.

    Args:
        worksheet: The worksheet where the footer will be generated.
        row_num: The starting row number for the footer.
    """
    column_counter = itertools.count(start=1)
    end_row = row_num + 4  # spans the footer title across multiple rows

    def build_footer_cell(
            value: str | int | float,
            is_number: bool = False,
            h_align: str | None = None,
    ):
        cell = cell_builder(
            worksheet=worksheet,
            row_num=row_num,
            column_num=next(column_counter),
            content=value,
            horizontal_alignment=h_align,
        )
        if is_number:
            cell.number_format = NUMBER_FORMAT
        return cell

    build_footer_cell("Total Sampai Halaman Ini", h_align="center")
    worksheet.merge_cells(
        start_row=row_num,
        start_column=1,
        end_row=end_row,
        end_column=2,
    )
