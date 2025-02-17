from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font
import itertools
import pandas as pd
from core.databases.gaji_batch_master_proses import get_nilai_komponen, get_total_nilai_komponen
from core.enums import STATUS_PEGAWAI
from core.excel_helper import cell_builder
from core.helper import get_nama_bulan
from core.helpers.himpunan_gaji.himpunan_gaji_direksi import generate_ttd


def generate_organisasi_sheet(
    workbook: Workbook,
    organisasi_df: pd.DataFrame,
    year: int,
    month: int,
    gaji_pegawai_df: pd.DataFrame,
    komponen_gaji_df: pd.DataFrame,
    dirum: pd.DataFrame,
) -> None:
    """
    Generate a sheet for each organisasi.
    """
    workbook.active = workbook["pegawai"]
    worksheet = workbook.active

    for _, organisasi in organisasi_df.iterrows():
        current_sheet = workbook.copy_worksheet(worksheet)
        current_sheet.title = organisasi["short_name"]
        current_sheet["A7"] = f"Bulan: {get_nama_bulan(month)} {year}"
        current_sheet["A8"] = organisasi["nama"]

        pegawai_df = gaji_pegawai_df[
            (gaji_pegawai_df["kode_organisasi"].str.startswith(
                organisasi["kode"]))
            & (gaji_pegawai_df["status_pegawai"] != STATUS_PEGAWAI.KONTRAK.value)
        ].reset_index(drop=True)

        pegawai_id_list = pegawai_df["id"].tolist()
        komponen_gaji_df_organisasi = komponen_gaji_df[
            komponen_gaji_df["master_batch_id"].isin(pegawai_id_list)
        ].reset_index(drop=True)

        generate_sheet_per_organisasi(
            current_sheet, pegawai_df, komponen_gaji_df_organisasi, dirum, year, month
        )


def generate_sheet_per_organisasi(
    worksheet: Worksheet, employees_df: pd.DataFrame, salary_components_df: pd.DataFrame, dirum: pd.DataFrame, year: int, month: int
):
    row_num = itertools.count(start=12)
    order_num = itertools.count(start=1)
    for _, employee in employees_df.iterrows():
        row_num = itertools.count(
            generate_organisasi_row(
                worksheet, next(row_num), next(
                    order_num), employee, salary_components_df
            )
        )

    row_num = itertools.count(
        generate_organisasi_footer(worksheet, next(
            row_num), employees_df, salary_components_df)
    )
    generate_ttd(worksheet, next(row_num), dirum, year, month)


def generate_organisasi_row(
    worksheet: Worksheet, row_number: int, order_number: int, row_data: dict, salary_components: pd.DataFrame
):
    row_counter = itertools.count(start=row_number)
    column_index = itertools.count(start=1)

    def build_cell(value, is_number=False, halign=None, valign=None):
        cell = cell_builder(
            worksheet=worksheet, row_num=row_number, column_num=next(column_index), content=value,
            h_aligment=halign, v_aligment=valign, border_option={
                "left": "thin", "right": "thin"
            }
        )
        if is_number:
            cell.number_format = "#,##0"

    build_cell(order_number)
    build_cell(
        f"{"** " if row_data["is_different"] else ""}{row_data["nama"]}")
    build_cell(row_data["nipam"])
    build_cell(row_data["golongan"] if row_data["golongan"]
               else "-", "center", "center")
    for index, component_list in enumerate([
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN",
            "POT_ASKES", "PENGHASILAN_BERSIH_FINAL"],
        ["", "", "", "", "TUNJ_SI", "0", "TUNJ_BERAS",
            "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["", "", "", "", "TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR",
            "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["", "", "", "", "JUMLAH", "", "TUNJ_KESEHATAN",
            "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]):
        current_row = next(row_counter)
        generate_cell_list(worksheet, current_row, 5 if index == 0 else 1,
                           salary_components, row_data, component_list, urut=order_number, is_first=index == 0, is_last=index == 3)

    return next(row_counter)


def generate_cell_list(worksheet: Worksheet, row_num: int, col_num: int,
                       salary_components: pd.DataFrame, row_data: dict, komponen_list: list,
                       urut: int = None, is_first=False, is_last=False):
    col_num = itertools.count(start=col_num)

    def build_cell(
        value: str, is_number: bool = False
    ):
        cell = cell_builder(worksheet, row_num, next(col_num), value, border_option={
                            "left": "thin", "right": "thin", "bottom": "thin" if is_last else None},)
        if is_number:
            cell.number_format = "#,##0"

    for komponen in komponen_list:
        if komponen == "0":
            build_cell(0, True)
        elif komponen == "":
            build_cell("")
        elif komponen == "JUMLAH":
            gaji_pokok = get_nilai_komponen(
                salary_components, row_data["id"], "GP")
            tunj_si = get_nilai_komponen(
                salary_components, row_data["id"], "TUNJ_SI")
            tunj_anak = get_nilai_komponen(
                salary_components, row_data["id"], "TUNJ_ANAK")
            jumlah = gaji_pokok + tunj_si + tunj_anak
            build_cell(jumlah, True)
        else:
            build_cell(get_nilai_komponen(salary_components,
                                          row_data["id"], komponen), True)
    if is_first:
        build_cell(str(urut))


def generate_organisasi_footer(worksheet: Worksheet, row_number: int, row_data: dict, salary_components: pd.DataFrame):
    generate_footer_title(worksheet, row_number, row_data)

    row_counter = itertools.count(start=row_number)

    for index, component_list in enumerate([
        ["GP", "0", "TUNJ_JABATAN", "TUNJ_AIR", "POT_PENSIUN",
            "POT_ASKES", "PENGHASILAN_BERSIH_FINAL", ""],
        ["TUNJ_SI", "0", "TUNJ_BERAS", "TUNJ_PPH21", "POT_ASTEK", "POT_TKK", "", ""],
        ["TUNJ_ANAK", "", "TUNJ_KK", "PENGHASILAN_KOTOR",
            "SEWA_RUDIN", "POT_PPH21", "", ""],
        ["JUMLAH", "", "TUNJ_KESEHATAN", "PEMBULATAN", "POT_JP", "POTONGAN", "", ""]
    ]):
        current_row = next(row_counter)
        generate_organisasi_footer_value(worksheet, current_row,
                                         salary_components, component_list, is_end=index == 3)

    next(row_counter)
    return next(row_counter)


def generate_footer_title(worksheet: Worksheet, row_num: int, row_data: dict):
    total_employees = row_data["id"].count()

    # Create and format the "DIREKSI" header cell
    direksi_cell = cell_builder(
        worksheet=worksheet,
        row_num=row_num,
        column_num=1,
        content="DIREKSI",
        v_aligment="center",
        border_option={
            "top": "thin",
            "bottom": "thin",
            "left": "thin",
            "right": "thin"
        }
    )
    direksi_cell.font = Font(bold=True)

    # Merge cells for the "DIREKSI" header
    worksheet.merge_cells(
        start_row=row_num,
        start_column=1,
        end_column=2,
        end_row=row_num + 3
    )

    # Create and format the "total employees" cell
    total_employees_cell = cell_builder(
        worksheet=worksheet,
        row_num=row_num,
        column_num=3,
        content=f"{total_employees} Pegawai",
        v_aligment="center",
        border_option={
            "top": "thin",
            "bottom": "thin",
            "left": "thin",
            "right": "thin"
        }
    )
    total_employees_cell.font = Font(bold=True)

    # Merge cells for the "total employees" cell
    worksheet.merge_cells(
        start_row=row_num,
        start_column=3,
        end_column=4,
        end_row=row_num + 3
    )

    return row_num+3


def generate_organisasi_footer_value(worksheet: Worksheet, row_num: int, salary_components: pd.DataFrame, komponen_list: list, is_end=False):
    col_num = itertools.count(start=5)

    def build_cell(value: str, is_number: bool = False) -> None:
        cell = cell_builder(
            worksheet=worksheet,
            row_num=row_num,
            column_num=next(col_num),
            content=value,
            border_option={
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if is_end else None
            }
        )
        if is_number:
            cell.number_format = "#,##0"

    for komponen in komponen_list:
        if komponen == "0":
            build_cell(0, True)
        elif komponen == "":
            build_cell("")
        elif komponen == "JUMLAH":
            gaji_pokok = get_total_nilai_komponen(
                salary_components, "GP")
            tunj_si = get_total_nilai_komponen(
                salary_components, "TUNJ_SI")
            tunj_anak = get_total_nilai_komponen(
                salary_components, "TUNJ_ANAK")
            jumlah = gaji_pokok + tunj_si + tunj_anak
            build_cell(jumlah, True)
        else:
            build_cell(get_total_nilai_komponen(
                salary_components, komponen), True)
