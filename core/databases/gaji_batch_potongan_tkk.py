import datetime

import pandas as pd
from core.config import get_connection_pool
from core.databases.riwayat_sp import fetch_riwayat_sp
from core.enums import STATUS_PEGAWAI, JENIS_SP
from icecream import ic


def fetch_all_gaji_batch_potongan_tkk_by_root_batch_id(root_batch_id: str):
    query = """
        SELECT nipam, sum(potongan) AS potongan 
        FROM 
            gaji_batch_potongan_tkk 
        WHERE 
            batch_id = %s
        GROUP BY
            nipam
        """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            return cursor.fetchall()


def fetch_gaji_potongan_tkk_by_root_batch_id_and_nipam(root_batch_id: str, nipam: str):
    query = """
            SELECT sum(potongan) AS potongan 
            FROM gaji_batch_potongan_tkk 
            WHERE batch_id = %s AND nipam = %s """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (root_batch_id, nipam))
            return cursor.fetchone()


def fetch_all_gaji_potongan_tkk():
    query = "SELECT id, status_pegawai, level_id, golongan_id, nominal FROM gaji_potongan_tkk"
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def filter_gaji_potongan_tkk(data: pd.DataFrame, status_pegawai: int, level_id: float, golongan_id: float):
    return data[(data["status_pegawai"] == status_pegawai) & (data["level_id"] == level_id) & (data["golongan_id"] == golongan_id)].reset_index(drop=True)


def fetch_gaji_potongan_tkk_by_status_pegawai(status_pegawai: int, level_id: int = None, golongan_id: int = None):
    parameters = [status_pegawai]
    query = "SELECT nominal FROM gaji_potongan_tkk WHERE status_pegawai = %s"

    if level_id and level_id < 7:
        query += " AND level_id = %s"
        parameters.append(int(level_id))

    if golongan_id and level_id == 7:
        query += " AND golongan_id = %s"
        parameters.append(int(golongan_id))

    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(parameters))
            return cursor.fetchone()


def get_jml_pot_tkk(root_batch_id: str, pegawai_id: int, nipam: str, status_pegawai: int):
    jumlah_potongan = 0
    periode = root_batch_id.split("-")[0]
    date_until = datetime.date(int(periode[0:4]), int(periode[4:6]), 20)
    timedelta_prev_month = datetime.timedelta(days=date_until.day)
    date_from = (date_until-timedelta_prev_month).strftime("%Y-%m-21")

    # check Riwayat SP
    riwayat_sp_data = fetch_riwayat_sp(pegawai_id, date_from, date_until)

    for row in riwayat_sp_data:
        # Jika pegawai kontrk kena SP 1,2,3
        if status_pegawai == STATUS_PEGAWAI.KONTRAK.value:
            if row["jenis_sp"] in (JENIS_SP.SP_1.value,
                                   JENIS_SP.SP_2.value,
                                   JENIS_SP.SP_3.value):
                jumlah_potongan = 11
                break
        if row["jenis_sp"] == JENIS_SP.SP_3.value:
            jumlah_potongan = -1
            break
        jumlah_potongan += row["nilai"]

    if jumlah_potongan > -1:
        # check potongan tkk
        potongan_tkk = fetch_gaji_potongan_tkk_by_root_batch_id_and_nipam(
            root_batch_id, nipam)
        if potongan_tkk["potongan"]:
            jumlah_potongan += int(potongan_tkk["potongan"])

    return jumlah_potongan


def calculate_jml_pot_tkk(riwayat_sp: pd.DataFrame, gaji_potongan_tkk: pd.DataFrame, pegawai_id: int, nipam: str, status_pegawai: float):
    jumlah_potongan = 0
    if not riwayat_sp.empty:
        filtered_riwayat_sp = riwayat_sp[riwayat_sp["pegawai_id"]
                                         == pegawai_id]
        if not filtered_riwayat_sp.empty:
            for _, row in filtered_riwayat_sp.iterrows():
                if status_pegawai == STATUS_PEGAWAI.KONTRAK.value:
                    if row["jenis_sp"] in {JENIS_SP.SP_1.value,
                                           JENIS_SP.SP_2.value,
                                           JENIS_SP.SP_3.value}:
                        jumlah_potongan = 11
                        break
                if row["jenis_sp"] == JENIS_SP.SP_3.value:
                    jumlah_potongan = -1
                    break
                jumlah_potongan += row["nilai"]

    if jumlah_potongan > -1:
        if gaji_potongan_tkk.empty:
            return jumlah_potongan
        
        gaji_potongan_tkk = gaji_potongan_tkk[gaji_potongan_tkk["nipam"] == nipam]
        if not gaji_potongan_tkk.empty:
            jumlah_potongan += gaji_potongan_tkk["potongan"].sum()

    return jumlah_potongan
