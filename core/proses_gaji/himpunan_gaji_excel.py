from openpyxl import load_workbook
from core.config import log_info
from core.databases.gaji_batch_master import fetch_daftar_gaji_pegawai
from core.databases.organisasi import fetch_organisasi_by_level
import pandas as pd
from core.helpers.himpunan_gaji.hg import generate_hg_sheet
from core.helpers.himpunan_gaji.hgpkp import generate_hgpkp_sheet
from core.helpers.himpunan_gaji.hhtkkp import generate_hhtkkp_sheet
from core.helpers.himpunan_gaji.himpunan_gaji_direksi import generate_direksi_sheet
from core.helpers.himpunan_gaji.himpunan_gaji_kontrak import generate_kontrak_sheets
from core.helpers.himpunan_gaji.himpunan_gaji_pegawai import generate_organisasi_sheet

def build(root_batch_id: str):
    log_info(f"generate himpunan gaji excel {root_batch_id}")
    organisasi_list = pd.DataFrame(fetch_organisasi_by_level([4]))

    raw_daftar_gaji_pegawai = pd.DataFrame(
        fetch_daftar_gaji_pegawai(root_batch_id))
    """
        create new data frame with raw_daftar gaji with column
            nipam,
            nama,
            golongan,
            jml_jiwa,
            gaji_pokok,
            penghasilan_bersih,
            kode_organisasi
        with unique nipam
    """
    daftar_gaji_pegawai = raw_daftar_gaji_pegawai[["id", "nipam", "nama", "status_pegawai", "golongan", "pangkat", "jml_tanggungan",
                                                   "jml_jiwa", "organisasi_id", "kode_organisasi", "nama_organisasi", "level_id", "is_different"]].drop_duplicates(subset=["nipam"]).reset_index(drop=True)
    daftar_gaji_pegawai["golongan"] = daftar_gaji_pegawai["golongan"].apply(
        lambda x: "" if x is None else x)
    daftar_gaji_pegawai["pangkat"] = daftar_gaji_pegawai["pangkat"].apply(
        lambda x: "" if x is None else x)
    daftar_proses_gaji_pegawai = raw_daftar_gaji_pegawai[[
        "master_batch_id", "kode", "jenis_gaji", "nilai", "uraian", "kode_organisasi"]].reset_index(drop=True)

    generate_excel(root_batch_id, organisasi_list,
                   daftar_gaji_pegawai, daftar_proses_gaji_pegawai)


def generate_excel(root_batch_id: str, organisasi_list: pd.DataFrame, daftar_gaji_pegawai: pd.DataFrame, daftar_proses_gaji_pegawai: pd.DataFrame):
    periode = root_batch_id.split("-")[0]
    tahun = int(periode[0:4])
    bulan = int(periode[4:6])
    wb = load_workbook("excel_template/daftar_gaji_template.xlsx")

    daftar_gaji_direksi = daftar_gaji_pegawai[
        daftar_gaji_pegawai["level_id"].isin([2, 3, 4])
    ].reset_index(drop=True)

    daftar_proses_gaji_direksi = daftar_proses_gaji_pegawai[
        daftar_proses_gaji_pegawai["master_batch_id"].isin(
            daftar_gaji_direksi["id"].tolist())
    ].reset_index(drop=True)

    dirum = daftar_gaji_pegawai[
        daftar_gaji_pegawai["level_id"] == 4
    ].reset_index(drop=True)

    generate_direksi_sheet(wb, tahun, bulan, daftar_gaji_direksi,
                           daftar_proses_gaji_direksi, dirum)

    generate_organisasi_sheet(wb, organisasi_list, tahun,
                              bulan, daftar_gaji_pegawai, daftar_proses_gaji_pegawai, dirum)

    generate_kontrak_sheets(wb, organisasi_list, tahun,
                            bulan, daftar_gaji_pegawai, daftar_proses_gaji_pegawai, dirum)

    generate_hgpkp_sheet(wb, organisasi_list, tahun, bulan,
                         daftar_gaji_pegawai, daftar_proses_gaji_pegawai)

    generate_hhtkkp_sheet(wb, organisasi_list, tahun, bulan,
                          daftar_gaji_pegawai, daftar_proses_gaji_pegawai)

    generate_hg_sheet(wb, organisasi_list, tahun, bulan,
                      daftar_gaji_pegawai, daftar_proses_gaji_pegawai)
    wb.remove(wb["pegawai"])
    wb.remove(wb["kontrak"])
    wb.remove(wb["HGPKP1"])
    wb.remove(wb["HHTKKP1"])
    wb.remove(wb["HG1"])
    wb.save(
        f"result_excel/tabel_gaji_{root_batch_id}.xlsx")
