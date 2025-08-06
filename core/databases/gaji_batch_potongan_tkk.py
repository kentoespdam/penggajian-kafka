import datetime

import pandas as pd
from core.config import get_connection_pool
from core.databases.riwayat_sp import fetch_riwayat_sp
from core.enums import STATUS_PEGAWAI, JENIS_SP


def fetch_all_gaji_batch_potongan_tkk_by_batch_root_id(batch_root_id: str):
    query = """
            SELECT nipam, sum(potongan) AS potongan
            FROM gaji_batch_potongan_tkk
            WHERE batch_id = %s
            GROUP BY nipam \
            """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (batch_root_id,))
            return cursor.fetchall()


def fetch_gaji_potongan_tkk_by_batch_root_id_and_nipam(
        batch_root_id: str, nipam: str) -> dict:
    """
    Fetches total potongan from gaji_batch_potongan_tkk by batch root id and nipam
    """
    query = """
            SELECT SUM(potongan) AS total_potongan
            FROM gaji_batch_potongan_tkk
            WHERE batch_id = %s
              AND nipam = %s
            """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (batch_root_id, nipam))
            result = cursor.fetchone()
            return dict(result) if result else None


def fetch_all_gaji_potongan_tkk():
    query = "SELECT id, status_pegawai, level_id, golongan_id, nominal FROM gaji_potongan_tkk"
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def filter_gaji_potongan_tkk(data: pd.DataFrame, status_pegawai: int, level_id: float, golongan_id: float):
    return data[(data["status_pegawai"] == status_pegawai) & (data["level_id"] == level_id) & (
            data["golongan_id"] == golongan_id)].reset_index(drop=True)


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


def get_jml_pot_tkk(batch_root_id: str, pegawai_id: int, nipam: str, status_pegawai: int) -> int:
    """Calculate the total deduction for a given nipam."""
    total_deduction = 0
    periode = batch_root_id.split("-")[0]
    end_date = datetime.date(
        int(periode[0:4]), int(periode[4:6]), 20)
    start_date = (end_date - datetime.timedelta(days=end_date.day)).strftime(
        "%Y-%m-21")

    # check Riwayat SP
    riwayat_sp_data = fetch_riwayat_sp(pegawai_id, start_date, end_date.strftime("%Y-%m-%d"))

    for row in riwayat_sp_data:
        # Jika pegawai kontrak kena SP 1,2,3
        if status_pegawai == STATUS_PEGAWAI.KONTRAK.value:
            if row["jenis_sp"] in (
                    JENIS_SP.SP_1.value, JENIS_SP.SP_2.value, JENIS_SP.SP_3.value):
                total_deduction = 11
                break
        if row["jenis_sp"] == JENIS_SP.SP_3.value:
            total_deduction = -1
            break
        total_deduction += row["nilai"]

    if total_deduction > -1:
        # check potongan tkk
        potongan_tkk = fetch_gaji_potongan_tkk_by_batch_root_id_and_nipam(
            batch_root_id, nipam)
        if potongan_tkk["potongan"]:
            total_deduction += int(potongan_tkk["potongan"])

    return total_deduction


def calculate_jml_pot_tkk(
        potongan_tkk_data: pd.DataFrame, nipam: str
) -> int:
    """
    Calculate the total deduction for a given nipam.
    """
    if potongan_tkk_data.empty:
        return 0

    total_deduction = 0
    filtered_potongan_tkk = potongan_tkk_data[potongan_tkk_data["nipam"] == nipam]

    if not filtered_potongan_tkk.empty:
        total_deduction = filtered_potongan_tkk["potongan"].sum()

    return total_deduction
