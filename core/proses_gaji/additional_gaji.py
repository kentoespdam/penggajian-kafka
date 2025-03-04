from math import ceil
from core.config import get_connection_pool
from core.databases.gaji_batch_master import fetch_gaji_batch_master_by_id
from core.databases.gaji_batch_master_proses import fetch_gaji_batch_master_proses_by_master_batch_id
from core.enums import JENIS_GAJI
import pandas as pd
from icecream import ic


def recalculate(master_batch_id: int):
    gaji_batch_master_proses_list = pd.DataFrame(fetch_gaji_batch_master_proses_by_master_batch_id(
        master_batch_id))

    add_tambahan = filter_add_gbp(
        gaji_batch_master_proses_list, JENIS_GAJI.PEMASUKAN.name)
    add_potongan = filter_add_gbp(
        gaji_batch_master_proses_list, JENIS_GAJI.POTONGAN.name)

    total_pemasukan = filter_gbp_by_jenis_gaji(
        gaji_batch_master_proses_list, "PEMASUKAN")
    total_potongan = filter_gbp_by_jenis_gaji(
        gaji_batch_master_proses_list, "POTONGAN")

    penghasilan_bersih2 = total_pemasukan-total_potongan
    pembulatan2 = (ceil(penghasilan_bersih2/100)*100)-penghasilan_bersih2
    penghasilan_bersih_final2 = penghasilan_bersih2+pembulatan2

    update_additional(add_tambahan, add_potongan, penghasilan_bersih2,
                      pembulatan2, penghasilan_bersih_final2, master_batch_id)


def filter_gbp_by_jenis_gaji(df: pd.DataFrame, jenis_gaji: str):
    filtered_data = df[(df["jenis_gaji"] == jenis_gaji)]
    return 0 if filtered_data.empty else float(filtered_data["nilai"].sum())


def filter_add_gbp(df: pd.DataFrame, jenis_gaji: str):
    filtered_data = df[(df["jenis_gaji"] == jenis_gaji) &
                       (df["kode"].str.startswith("ADD_"))]
    return 0 if filtered_data.empty else float(filtered_data["nilai"].sum())


def update_additional(
        add_tambahan: float,
        add_potongan: float,
        penghasilan_bersih2: float,
        pembulatan2: float,
        penghasilan_bersih_final2: float,
        master_batch_id: int):
    query = """
            UPDATE gaji_batch_master SET
                total_add_tambahan = %s,
                total_add_potongan = %s,
                penghasilan_bersih2 = %s,
                pembulatan2 = %s,
                penghasilan_bersih_final2 = %s
            WHERE id = %s
        """
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (add_tambahan, add_potongan, penghasilan_bersih2,
                           pembulatan2, penghasilan_bersih_final2, master_batch_id))
            conn.commit()
            ic("update gaji batch master ", cursor.rowcount, "affected rows")
