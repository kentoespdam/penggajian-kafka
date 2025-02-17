import itertools
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles.fonts import Font
from openpyxl.styles.alignment import Alignment
import pandas as pd
from core.databases.gaji_batch_master_proses import get_total_nilai_komponen
from core.enums import STATUS_PEGAWAI
from core.excel_helper import cell_builder

def generate_hhtkkp_sheet(
    workbook: Workbook, organisasi_df: pd.DataFrame, year: int, month: int,
    gaji_pegawai_df: pd.DataFrame, komponen_gaji_df: pd.DataFrame
) -> None:
    workbook.active = workbook["HHTKKP1"]
    worksheet = workbook.copy_worksheet(workbook.active)
    worksheet.title = "HHTKKP"

    organisasi_df = organisasi_df[~organisasi_df["nama"].str.startswith(
        "CABANG")].reset_index(drop=True)

    gaji_pegawai_df = gaji_pegawai_df[gaji_pegawai_df["status_pegawai"]
                                      == STATUS_PEGAWAI.KONTRAK.value].reset_index(drop=True)
    gaji_pegawai_df["kode_organisasi"] = gaji_pegawai_df["kode_organisasi"].apply(
        lambda x: x[:3] if len(x) == 5 else x[:5])
    organisasi_df = organisasi_df[organisasi_df["kode"].isin(
        gaji_pegawai_df["kode_organisasi"].unique().tolist())].reset_index(drop=True)
    gaji_pegawai_df = gaji_pegawai_df[gaji_pegawai_df["kode_organisasi"].isin(
        organisasi_df["kode"].tolist())].reset_index(drop=True)

    komponen_gaji_df = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
        gaji_pegawai_df["id"].tolist())].reset_index(drop=True)

    row_num = itertools.count(start=12)
    for index, organisasi in organisasi_df.iterrows():
        current_pegawai = gaji_pegawai_df[gaji_pegawai_df["kode_organisasi"].str.startswith(
            organisasi["kode"])].reset_index(drop=True)
        current_komponen_gaji = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
            current_pegawai["id"].tolist())].reset_index(drop=True)
        generate_row(worksheet, next(row_num), current_komponen_gaji,
                     organisasi["nama"], index+1)

    generate_row(worksheet, next(row_num), komponen_gaji_df, "JUMLAH")


def generate_row(
        worksheet: Worksheet, row_num: int, salary_components_df: pd.DataFrame,
        organisasi_name: str, urut: int = None):
    column_index = itertools.count(start=1)
    is_bold = False

    def build_cell(value, is_number=False, halign=None, valign=None):
        cell = cell_builder(
            worksheet=worksheet, row_num=row_num, column_num=next(column_index), content=value,
            h_aligment=halign, v_aligment=valign, border_option={
                "left": "thin", "right": "thin", "bottom": "thin"
            }
        )
        if is_number:
            cell.number_format = "#,##0"
        if is_bold:
            cell.font = Font(bold=True)
        return cell
    if urut and organisasi_name != "JUMLAH":
        is_bold = False
        build_cell(urut, True)
        build_cell(organisasi_name)
    else:
        is_bold = True
        current_cell = build_cell(organisasi_name)
        next(column_index)
        worksheet.merge_cells(
            start_row=row_num, start_column=1, end_row=row_num, end_column=2)
        current_cell.alignment = Alignment(horizontal="center")

    for komponen in ["GP", "POT_ASTEK", "POT_JP", "POT_ASKES", 0, "POTONGAN", "PENGHASILAN_BERSIH_FINAL", ""]:
        build_cell(get_total_nilai_komponen(
            salary_components_df, komponen), True)
