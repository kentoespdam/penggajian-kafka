import itertools
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles.fonts import Font
from openpyxl.styles.alignment import Alignment
import pandas as pd

from core.databases.gaji_batch_master_proses import get_total_nilai_komponen
from core.enums import STATUS_PEGAWAI
from core.excel_helper import cell_builder
from core.helper import get_nama_bulan
from icecream import ic


def generate_hg_sheet(workbook: Workbook, organisasi_df: pd.DataFrame, year: int, month: int,
                      gaji_pegawai_df: pd.DataFrame, komponen_gaji_df: pd.DataFrame) -> None:
    """
    Generate HG sheet for given parameters.
    """
    workbook.active = workbook["HG1"]
    worksheet = workbook.copy_worksheet(workbook.active)
    worksheet.title = "HG"

    kontrak_df = gaji_pegawai_df[gaji_pegawai_df["status_pegawai"]
                                 == STATUS_PEGAWAI.KONTRAK.value].reset_index(drop=True)

    # Cabang
    organisasi_cabang_df = organisasi_df[organisasi_df["nama"].str.startswith(
        "CABANG")].reset_index(drop=True)
    pegawai_cabang_df = gaji_pegawai_df[
        (gaji_pegawai_df["kode_organisasi"].str.startswith(tuple(organisasi_cabang_df["kode"].unique().tolist()))) &
        (gaji_pegawai_df["status_pegawai"] != STATUS_PEGAWAI.KONTRAK.value)
    ].reset_index(drop=True)
    komponen_cabang_df = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
        pegawai_cabang_df["id"])]
    kontrak_cabang_df = kontrak_df[kontrak_df["kode_organisasi"].str.startswith(
        tuple(organisasi_cabang_df["kode"].unique().tolist()))].reset_index(drop=True)

    # Pusat
    organisasi_pusat_df = organisasi_df[~organisasi_df["id"].isin(
        organisasi_cabang_df["id"])]
    pegawai_pusat_df = gaji_pegawai_df[
        ((gaji_pegawai_df["status_pegawai"] != STATUS_PEGAWAI.KONTRAK.value) &
         (gaji_pegawai_df["kode_organisasi"].str.startswith(tuple(organisasi_pusat_df["kode"].unique().tolist()))) |
         gaji_pegawai_df["level_id"].isin([2, 3, 4]))
    ].reset_index(drop=True)
    kontrak_pusat_df = kontrak_df[kontrak_df["kode_organisasi"].str.startswith(
        tuple(organisasi_pusat_df["kode"].unique().tolist()))].reset_index(drop=True)

    # Filter komponen gaji by cabang and pusat

    komponen_kontrak_cabang_df = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
        kontrak_cabang_df["id"])]
    komponen_kontrak_cabang_df.loc[:,
                                   "kode_organisasi"] = komponen_kontrak_cabang_df["kode_organisasi"].str[:3]

    komponen_pusat_df = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
        pegawai_pusat_df["id"])]
    komponen_kontrak_pusat_df = komponen_gaji_df[komponen_gaji_df["master_batch_id"].isin(
        kontrak_pusat_df["id"])]

    # Generate rows in the worksheet
    row_counter = itertools.count(start=7)
    order_counter = itertools.count(start=1)
    next_row, next_order = generate_gapok_row(
        worksheet,
        next(row_counter),
        komponen_pusat_df,
        komponen_cabang_df,
        komponen_kontrak_pusat_df,
        komponen_kontrak_cabang_df,
        next(order_counter)
    )
    row_counter = itertools.count(start=next_row)
    order_counter = itertools.count(start=next_order)

    next_row, next_order = generate_tunjangan_row(
        worksheet,
        next(row_counter),
        komponen_pusat_df,
        komponen_cabang_df,
        next(order_counter),
    )
    row_counter = itertools.count(start=next_row)
    order_counter = itertools.count(start=next_order)

    next_row=generate_penghasilan_kotor_row(worksheet, next(row_counter))

    row_counter = itertools.count(start=next_row)


def generate_gapok_row(
    worksheet: Worksheet,
    start_row: int,
    pusat_gaji: pd.DataFrame,
    cabang_gaji: pd.DataFrame,
    pusat_kontrak_gaji: pd.DataFrame,
    cabang_kontrak_gaji: pd.DataFrame,
    start_urut: int,
) -> tuple[int, int]:
    """
    Generate HG sheet rows for gapok data.
    """
    row_num = itertools.count(start=start_row)
    urut = itertools.count(start=start_urut)
    # row Gaji Pokok
    generate_row(
        worksheet,
        next(row_num),
        pusat_gaji,
        cabang_gaji,
        "GP",
        "Gaji Pokok",
        next(urut),
    )
    # row Kontrak
    generate_row(
        worksheet,
        next(row_num),
        pusat_kontrak_gaji,
        cabang_kontrak_gaji,
        "GP",
        "Honor Tenaga Kontrak",
        next(urut),
    )
    generate_empty_row(worksheet, next(row_num), 9)
    generate_empty_row(worksheet, next(row_num), 9)

    return next(row_num), next(urut)


def generate_tunjangan_row(
    worksheet: Worksheet, start_row: int, central_gaji: pd.DataFrame, branch_gaji: pd.DataFrame, start_order: int
) -> tuple[int, int]:
    """
    Generate HG sheet rows for tunjangan data.
    """
    row_num = itertools.count(start=start_row)
    order = itertools.count(start=start_order)
    empty_row_num = next(row_num)
    generate_empty_row(worksheet, empty_row_num, 9)
    tunjangan_cell = worksheet.cell(row=empty_row_num, column=2)
    tunjangan_cell.value = "Tunjangan:"
    tunjangan_cell.font = Font(bold=True)

    def build_row(kode: str, description: str) -> None:
        generate_row(
            worksheet,
            next(row_num),
            central_gaji,
            branch_gaji,
            kode,
            description,
            next(order),
        )

    # row Tunjangan
    build_row("TUNJ_SI", "Istri/Suami")
    build_row("TUNJ_ANAK", "Anak")
    build_row("TUNJ_JABATAN", "Jabatan / Pelaksana")
    build_row("TUNJ_BERAS", "Beras")
    build_row("TUNJ_KK", "Kegiatan Kerja")
    build_row("TUNJ_AIR", "Air")
    build_row("TUNJ_PPH21", "P.Ph. Pasal 21")
    build_row("PEMBULATAN", "Pembulatan")
    generate_empty_row(worksheet, next(row_num), 9)
    # generate_row(
    #     worksheet,
    #     next(row_num),
    #     central_gaji,
    #     branch_gaji,
    #     "PENGHASILAN_KOTOR",
    #     "Jumlah Penghasilan Kotor",
    #     is_bold=True
    # )
    return next(row_num), next(order)


def generate_penghasilan_kotor_row(worksheet: Worksheet, row_num: int) -> int:
    column_index = itertools.count(start=1)

    def build_cell(content: str, is_number: bool = False) -> None:
        """
        Build a cell in the worksheet.
        """
        cell = cell_builder(
            worksheet,
            row_num,
            next(column_index),
            content,
            border_option={"left": "thin", "right": "thin", "bottom": "thin"},
        )
        cell.font = Font(bold=True)
        if is_number:
            cell.number_format = "#,##0"
        return cell
    
    build_cell("")
    build_cell("Jumlah Penghasilan Kotor")
    build_cell(f"=SUM(C{7}:C{row_num-1})", True)
    build_cell(f"=SUM(D{7}:D{row_num-1})", True)
    build_cell(f"=SUM(E{7}:E{row_num-1})", True)
    build_cell(f"=SUM(F{7}:F{row_num-1})", True)
    build_cell(f"=SUM(G{7}:G{row_num-1})", True)
    build_cell(f"=SUM(H{7}:H{row_num-1})", True)
    build_cell(f"=SUM(I{7}:I{row_num-1})", True)

    return row_num+1


def generate_row(
        worksheet: Worksheet,
        row_number: int,
        central_gaji_components: pd.DataFrame,
        branch_gaji_components: pd.DataFrame,
        component_code: str,
        component_description: str,
        order: int = None,
        is_bold: bool = False
) -> None:
    """
    Generate a row in HG sheet for a given component.
    """
    column_index = itertools.count(start=1)

    def build_cell(content: str, is_number: bool = False) -> None:
        """
        Build a cell in the worksheet.
        """
        cell = cell_builder(
            worksheet,
            row_number,
            next(column_index),
            content,
            border_option={"left": "thin", "right": "thin", "bottom": "thin"},
        )
        if is_number:
            cell.number_format = "#,##0"
        if is_bold:
            cell.font = Font(bold=True)
        return cell

    build_cell(order)
    build_cell(component_description)

    central_filtered = filter_gaji_components_by_code(
        central_gaji_components, component_code)
    branch_filtered = filter_gaji_components_by_code(
        branch_gaji_components, component_code)

    # Generate Gaji Pokok Pusat
    build_cell(central_filtered["nilai"].sum(), True)
    # Generate Gaji Pokok Cabang
    build_cell(
        branch_filtered[branch_filtered["kode_organisasi"].str.startswith(
            "1.4")]["nilai"].sum(),  # Cabang Pwt-1
        True,
    )
    build_cell(
        branch_filtered[branch_filtered["kode_organisasi"].str.startswith(
            "1.5")]["nilai"].sum(),  # Cabang Pwt-2
        True,
    )
    build_cell(
        branch_filtered[branch_filtered["kode_organisasi"].str.startswith(
            "1.8")]["nilai"].sum(),  # Cabang Ajb
        True,
    )
    build_cell(
        branch_filtered[branch_filtered["kode_organisasi"].str.startswith(
            "1.7")]["nilai"].sum(),  # Cabang Wgn
        True,
    )
    build_cell(
        branch_filtered[branch_filtered["kode_organisasi"].str.startswith(
            "1.6")]["nilai"].sum(),  # Cabang Bms
        True,
    )
    # Generate Gaji Pokok Total
    build_cell(
        central_filtered["nilai"].sum() + branch_filtered["nilai"].sum(), True)


def generate_empty_row(worksheet: Worksheet, row_num: int, col_count: int = 1) -> None:
    """Generate an empty row in the given worksheet at the given row_num."""
    for col_index in range(1, col_count + 1):
        cell_builder(
            worksheet, row_num, col_index, "",
            border_option={"left": "thin", "right": "thin", "bottom": "thin"}
        )


def filter_gaji_components_by_code(gaji_components_df: pd.DataFrame, code: str) -> pd.DataFrame:
    """Filter gaji components by code."""
    return gaji_components_df[gaji_components_df["kode"] == code].reset_index(drop=True)
