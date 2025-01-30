import datetime
import pandas as pd
from core.config import ENGINE, POOL
from core.enums import JENIS_SP, STATUS_PEGAWAI, TUNJANGAN
from icecream import ic

from gaji_batch_potongan_tkk import get_potongan_tkk_data
from riwayat_sp import get_riwayat_sp_data


def get_gaji_komponen_data(profil_gaji_id: int = None) -> list:
    """
    Fetch Gaji Komponen data by profil gaji ID.
    Args:
        profil_gaji_id (int, optional): Profil gaji ID. Defaults to None.
    Returns:
        list: Gaji Komponen data.
    """
    parameters = ()
    query = """
        SELECT
            gk.id,
            gk.profil_gaji_id,
            gk.urut,
            gk.kode,
            gk.nama,
            gk.nilai,
            gk.formula,
            gk.jenis_gaji,
            gk.is_reference,
            gp.nama AS nama_profil
        FROM
            gaji_komponen AS gk
            INNER JOIN gaji_profil AS gp ON gk.profil_gaji_id = gp.id AND gp.is_deleted = FALSE
        WHERE
            gk.is_deleted = FALSE
    """
    if profil_gaji_id:
        query += " AND gk.profil_gaji_id = %s"
        parameters = (profil_gaji_id,)

    query += """ ORDER BY gk.urut ASC"""
    data = None
    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            data = cursor.fetchall()

    return data


def get_parameter_setting_data(kode: str = None):
    sql = """
        SELECT
            kode,
            nominal
        FROM
            gaji_parameter_setting
        WHERE is_deleted = FALSE
        """
    parameters = ()
    if kode:
        sql += " AND kode = %s"
        parameters = (kode,)

    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, parameters)
            data = cursor.fetchone() if kode else cursor.fetchall()
    return data


def get_nominal_parameter(data: pd.DataFrame, kode: str):
    return data.loc[data["kode"] == kode, "nominal"].values[0]


def get_gaji_phdp_formula(tmt_kerja: datetime, tmt_pensiun: datetime):
    tmt_kerja_str = tmt_kerja.strftime("%Y%m%d")
    tmt_pensiun_str = tmt_pensiun.strftime("%Y%m%d")
    sql = """
        SELECT
            kondisi,
            formula
        FROM
            gaji_phdp
        WHERE 
            is_deleted = FALSE
        ORDER BY
            urut ASC
        """
    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
    for row in data:
        kondisi = row["kondisi"]
        kondisi = kondisi.replace("&&", "and").replace(
            "MASA_KERJA", tmt_kerja_str).replace("PENSIUN", tmt_pensiun_str)
        result = eval(kondisi)
        if result:
            formula = row["formula"]
            break
        else:
            formula = ""
    # ic(formula)
    return formula


def get_tunjangan_data(reference: int, level_id: int = None, golongan_id: int = None):
    parameters = {"reference": reference,
                  "level_id": level_id,
                  "golongan_id": golongan_id}
    sql = """
        SELECT id, jenis_tunjangan, level_id, golongan_id, nominal
        FROM gaji_tunjangan
        WHERE jenis_tunjangan = %(reference)s
        """
    if level_id in [5, 6] and reference == TUNJANGAN.BERAS.value:
        sql += " AND level_id = %(level_id)s"
    else:
        sql += " AND golongan_id = %(golongan_id)s"

    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, args=parameters)
            data = cursor.fetchone() if level_id or golongan_id else cursor.fetchall()
    return data


def get_tunjangan_value(ref: pd.DataFrame, level_id: int, golongan_id: float):
    ic(level_id, golongan_id)
    for _, row in ref.iterrows():
        if level_id == 7 and row["golongan_id"] == golongan_id:
            return row["nominal"]
        if level_id == row["level_id"]:
            return row["nominal"]

    pass


def get_rumah_dinas_data(rumah_dinas_id: int):
    sql = """
        SELECT
            nilai as nominal
        FROM
            rumah_dinas
        WHERE 
            is_deleted = FALSE
            AND id = %s
        """
    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (rumah_dinas_id,))
            data = cursor.fetchone()
    return data

