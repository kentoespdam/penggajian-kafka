import json

from core.config import get_connection_pool
from core.enums import EProsesGaji
import pandas as pd
from icecream import ic

def fetch_gaji_batch_root_by_id(batch_root_id):
    query = "SELECT * FROM gaji_batch_root WHERE is_deleted = %s AND id = %s"
    params = (False, batch_root_id)
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()


def update_status_gaji_batch_root(batch_root_id: str, status_process: int, total_pegawai: int = 0, notes: str = "") -> None:
    query = "UPDATE gaji_batch_root SET status = %s"
    params = [status_process]
    if total_pegawai > 0:
        query += ", total_pegawai = %s"
        params.append(total_pegawai)
    if notes:
        query += ", notes = %s"
        params.append(json.dumps(notes))
    if status_process == EProsesGaji.PROSES.value:
        query += ", tanggal_proses = CURRENT_TIMESTAMP"

    query += " WHERE id = %s"
    params.append(batch_root_id)
    
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            conn.commit()
