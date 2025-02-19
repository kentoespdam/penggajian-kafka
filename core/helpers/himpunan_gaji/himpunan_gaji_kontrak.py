import itertools
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font
import pandas as pd
from icecream import ic
from core.databases.gaji_batch_master_proses import get_nilai_komponen, get_total_nilai_komponen
from core.enums import STATUS_PEGAWAI
from core.excel_helper import cell_builder
from core.helper import get_nama_bulan
from core.helpers.himpunan_gaji.himpunan_gaji_direksi import generate_ttd
import swifter

def generate_kontrak_sheets(workbook: Workbook, organisasi_df: pd.DataFrame, year: int, month: int,
                            gaji_kontrak_df: pd.DataFrame, komponen_gaji_df: pd.DataFrame,
                            dirum: pd.DataFrame) -> None:
    """
    Generate a sheet for each organisasi based on the given parameters.
    """
    kontrak_df = gaji_kontrak_df[gaji_kontrak_df["status_pegawai"]
                                 == STATUS_PEGAWAI.KONTRAK.value].reset_index(drop=True)
    kontrak_df["kode_organisasi"] = kontrak_df["kode_organisasi"].swifter.apply(
        lambda x: x[:3] if len(x) == 5 else x[:5])

    kontrak_org_codes = kontrak_df["kode_organisasi"].unique().tolist()
    organisasi_df = organisasi_df[organisasi_df["kode"].isin(
        kontrak_org_codes)].reset_index(drop=True)

    workbook.active = workbook["kontrak"]
    template_sheet = workbook.active

    for _, organisasi in organisasi_df.iterrows():
        current_sheet = workbook.copy_worksheet(template_sheet)
        current_sheet.title = f"KONTRAK-{organisasi['short_name']}"
        current_sheet["A7"] = f"Bulan: {get_nama_bulan(month)} {year}"
        current_sheet["A8"] = organisasi["nama"]

        pegawai_df = kontrak_df[kontrak_df["kode_organisasi"]
                                == organisasi["kode"]].reset_index(drop=True)
        pegawai_ids = pegawai_df["id"].tolist()
        komponen_gaji_df_organisasi = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
            pegawai_ids)].reset_index(drop=True)

        generate_sheet_per_organisasi(
            current_sheet, pegawai_df, komponen_gaji_df_organisasi, dirum, year, month
        )


def generate_sheet_per_organisasi(worksheet: Worksheet, employees_df: pd.DataFrame, salary_components_df: pd.DataFrame, dirum: pd.DataFrame, year: int, month: int):
    row_num = itertools.count(start=12)
    for index, employee in employees_df.iterrows():
        current_row_num = next(row_num)
        col_num = itertools.count(1)
        cell_builder(worksheet, current_row_num, next(col_num), index+1, border_option={
                     "left": "thin", "right": "thin", "bottom": "thin"})
        cell_builder(worksheet, current_row_num, next(col_num),
                     f"{'** ' if employee['is_different'] else ''}{employee['nama']}", border_option={
                         "left": "thin", "right": "thin", "bottom": "thin"})
        net_col_num = generate_organisasi_row(
            worksheet, current_row_num, next(
                col_num), employee, salary_components_df
        )
        col_num = itertools.count(start=net_col_num)
        cell_builder(worksheet, current_row_num, next(col_num), f"{index+1}", border_option={
                     "left": "thin", "right": "thin", "bottom": "thin"})

    generate_footer(worksheet, next(row_num), salary_components_df)
    next(row_num)
    generate_ttd(worksheet, next(row_num), dirum, year, month)


def generate_organisasi_row(
        worksheet: Worksheet,
        row_num: int,
        col_num: int,
        employee: pd.Series,
        salary_components_df: pd.DataFrame) -> int:
    col_num = itertools.count(col_num)

    def build_cell(value: str, is_number: bool = False):
        cell = cell_builder(worksheet, row_num, next(col_num), value, border_option={
                            "left": "thin", "right": "thin", "bottom": "thin"})
        if is_number:
            cell.number_format = "#,##0"

    for komponen in ["GP", "POT_ASTEK", "POT_JP", "POT_ASKES", 0, "POTONGAN", "PEMBULATAN", "PENGHASILAN_BERSIH_FINAL"]:
        build_cell(get_nilai_komponen(
            salary_components_df, employee["id"], komponen), True)
    return next(col_num)


def generate_footer(worksheet: Worksheet, row_num: int, salary_components_df: pd.DataFrame):
    col_num = itertools.count(1)

    def build_cell(value: str, is_number: bool = False, h_align: str = None):
        cell = cell_builder(worksheet, row_num, next(col_num), value, h_aligment=h_align, border_option={
                            "left": "thin", "right": "thin", "bottom": "thin"})
        if is_number:
            cell.number_format = "#,##0"

        return cell

    build_cell("JUMLAH", h_align="center").font = Font(bold=True)
    worksheet.merge_cells(start_row=row_num, start_column=1,
                          end_column=next(col_num), end_row=row_num)
    for komponen in ["GP", "POT_ASTEK", "POT_JP", "POT_ASKES", 0, "POTONGAN", "PEMBULATAN", "PENGHASILAN_BERSIH_FINAL"]:
        build_cell(get_total_nilai_komponen(
            salary_components_df, komponen), True)
    build_cell("")
