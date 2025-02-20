import json
from core.config import get_connection_pool
from core.enums import EProsesGaji


def fetch_gaji_batch_root_by_batch_id(batch_id: str) -> tuple:
    """Fetch GajiBatchRoot by batch ID."""
    query = "SELECT * FROM gaji_batch_root WHERE is_deleted = false AND batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (batch_id,))
            return cursor.fetchone()

def update_status_gaji_batch_root(root_batch_id: str, status_process: int, total_pegawai: int = 0, notes: dict = None):
    query = """
                UPDATE gaji_batch_root
                SET
                    total_pegawai = %s,
                    notes=%s,
                    status = %s
                """
    if status_process == EProsesGaji.PROSES.value:
        query += ", tanggal_proses = NOW()"

    query += " WHERE batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (total_pegawai, json.dumps(
                notes) if notes else None, status_process, root_batch_id))
            conn.commit()


def delete_batch_root_error_logs_by_root_batch_id(root_batch_id: str):
    query = "DELETE FROM gaji_batch_root_error_logs WHERE root_batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            conn.commit()

def exists_gaji_batch_root_by_batch_id(batch_id: str) -> bool:
    query = """
        SELECT COUNT(*) AS jml
        FROM gaji_batch_root
        WHERE batch_id = %s
        AND is_deleted = FALSE
        AND status > 1
    """
    with get_connection_pool() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (batch_id,))
            result = cursor.fetchone()
            return  result["jml"]>0 if result else 0
