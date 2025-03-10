import datetime
from openpyxl import load_workbook
from core.databases.gaji_batch_master import fetch_daftar_gaji_pegawai, fetch_daftar_potongan_gaji_by_batch_root_id
from core.databases.organisasi import fetch_organisasi_by_level
import pandas as pd
from core.helpers.potongan_gaji.potongan_gaji_helper import generate_potongan
from icecream import ic


def main(batch_root_id: str):
    organisasi_list = pd.DataFrame(fetch_organisasi_by_level([4]))
    daftar_potongan_gaji_df = pd.DataFrame(fetch_daftar_potongan_gaji_by_batch_root_id(
        batch_root_id))
    generate_excel(batch_root_id, organisasi_list, daftar_potongan_gaji_df)


def generate_excel(batch_root_id: str, organisasi_list: pd.DataFrame, daftar_potongan_gaji_pegawai: pd.DataFrame):
    periode = batch_root_id.split("-")[0]
    tahun = int(periode[0:4])
    bulan = int(periode[4:6])
    wb = load_workbook("excel_template/potongan_gaji_template.xlsx")

    potongan_gaji_direksi_df = daftar_potongan_gaji_pegawai[daftar_potongan_gaji_pegawai["level_id"].isin(
        [2, 3, 4])].reset_index(drop=True)

    generate_potongan(
        wb, "DIREKSI", "DIREKSI", tahun, bulan, potongan_gaji_direksi_df)

    for _, organisasi in organisasi_list.iterrows():
        potongan_gaji_pegawai = daftar_potongan_gaji_pegawai[
            daftar_potongan_gaji_pegawai["kode_organisasi"].str.startswith(
                organisasi["kode"])
        ].reset_index(drop=True)
        generate_potongan(
            wb, organisasi["nama"], organisasi["short_name"], tahun, bulan, potongan_gaji_pegawai)

    wb.save(
        f"result_excel/potongan_gaji_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")


if __name__ == "__main__":
    main("202402-001")
