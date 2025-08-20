import itertools
from dataclasses import dataclass

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from core.config import KODE_CABANG_PWT1, KODE_CABANG_PWT2, KODE_CABANG_AJB, KODE_CABANG_WGN, KODE_CABANG_BMS
from core.excel_helper import cell_builder, NUMBER_FORMAT, copy_sheet_from_template
from core.helpers import get_nama_bulan
from core.process_gaji.phase3_generate_hg_filter import filter_gaji_komponen_by_kode, get_nilai_by_cabang

COLUMN_COUNT = 9


@dataclass(frozen=True)
class KomponenData:
    pegawai_pusat: pd.DataFrame
    pegawai_cabang: pd.DataFrame
    kontrak_pusat: pd.DataFrame
    kontrak_cabang: pd.DataFrame


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


def prepare_hg_worksheet(workbook: Workbook, year: int, month: int) -> Worksheet:
    _TEMPLATE_SHEET_NAME = "HG1"
    _OUTPUT_SHEET_NAME = "HG"
    _HEADER_ROW = 1
    _HEADER_COL = 1

    ws = copy_sheet_from_template(workbook, _TEMPLATE_SHEET_NAME, _OUTPUT_SHEET_NAME)
    ws.cell(row=_HEADER_ROW, column=_HEADER_COL, value=f"Bulan: {get_nama_bulan(month)} {year}")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)
    return ws


def generate_empty_row(worksheet: Worksheet, row_num: int, column_count: int):
    for col_index in range(1, column_count + 1):
        cell_builder(worksheet, row_num, col_index, "", border={"left": "thin", "right": "thin", "bottom": "thin"})


def generate_row(worksheet: Worksheet, row_num: int, data_pusat_df: pd.DataFrame, data_cabang_df: pd.DataFrame,
                 kode: str,
                 kode_description: str, order: int | None = None,
                 font_bold: bool = False, with_pembulatan: bool = False):
    column_counter = itertools.count(start=1)

    def build_cell(value: str | int | float, is_number: bool = False):
        cell = cell_builder(worksheet, row_num, next(column_counter), value, font_bold,
                            border={"left": "thin", "right": "thin", "bottom": "thin"})
        if is_number:
            cell.number_format = NUMBER_FORMAT
        return cell

    build_cell(order or "")
    build_cell(kode_description)

    komponen_gaji_pusat_df = filter_gaji_komponen_by_kode(data_pusat_df, kode)
    komponen_gaji_cabang_df = filter_gaji_komponen_by_kode(data_cabang_df, kode)

    # Generate Pusat
    total_pusat = get_nilai_by_cabang(komponen_gaji_pusat_df)
    total_cabang_pwt1 = get_nilai_by_cabang(komponen_gaji_cabang_df, KODE_CABANG_PWT1)
    total_cabang_pwt2 = get_nilai_by_cabang(komponen_gaji_cabang_df, KODE_CABANG_PWT2)
    total_cabang_ajb = get_nilai_by_cabang(komponen_gaji_cabang_df, KODE_CABANG_AJB)
    total_cabang_wgn = get_nilai_by_cabang(komponen_gaji_cabang_df, KODE_CABANG_WGN)
    total_cabang_bms = get_nilai_by_cabang(komponen_gaji_cabang_df, KODE_CABANG_BMS)
    total_cabang = get_nilai_by_cabang(komponen_gaji_cabang_df)

    if with_pembulatan:
        komponen_pembulatan_pusat = filter_gaji_komponen_by_kode(data_pusat_df, "PEMBULATAN")
        komponen_pembulatan_cabang = filter_gaji_komponen_by_kode(data_cabang_df, "PEMBULATAN")
        total_pusat += get_nilai_by_cabang(komponen_pembulatan_pusat)
        total_cabang_pwt1 += get_nilai_by_cabang(komponen_pembulatan_cabang, KODE_CABANG_PWT1)
        total_cabang_pwt2 += get_nilai_by_cabang(komponen_pembulatan_cabang, KODE_CABANG_PWT2)
        total_cabang_ajb += get_nilai_by_cabang(komponen_pembulatan_cabang, KODE_CABANG_AJB)
        total_cabang_wgn += get_nilai_by_cabang(komponen_pembulatan_cabang, KODE_CABANG_WGN)
        total_cabang_bms += get_nilai_by_cabang(komponen_pembulatan_cabang, KODE_CABANG_BMS)
        total_cabang += get_nilai_by_cabang(komponen_pembulatan_cabang)

    build_cell(total_pusat, True)
    # Generate Cabang
    # Cabang PWT1

    build_cell(total_cabang_pwt1, True)
    # Cabang PWT2
    build_cell(total_cabang_pwt2, True)
    # Cabang AJB
    build_cell(total_cabang_ajb, True)
    # Cabang WGN
    build_cell(total_cabang_wgn, True)
    # Cabang BMS
    build_cell(total_cabang_bms, True)

    # Generate Total
    total = total_pusat + total_cabang
    build_cell(total, True)


def generate_section_title(worksheet: Worksheet, pos: PositionTracker, title: str) -> None:
    """
    Generate the title row for the Tunjangan section.
    """
    title_row_number = pos.next_row()
    generate_empty_row(worksheet, title_row_number, COLUMN_COUNT)
    tunjangan_cell = worksheet.cell(row=title_row_number, column=2)
    tunjangan_cell.value = title
    tunjangan_cell.font = Font(bold=True)
