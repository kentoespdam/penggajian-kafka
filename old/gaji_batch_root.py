import json
from core.config import POOL


def update_status_gaji_batch_root(
        root_batch_id: str,
        status_process: int,
        total_pegawai: int = 0,
        notes: dict = None
):
    pass
    sql_update = """
                UPDATE gaji_batch_root
                SET
                    total_pegawai = %s,
                    notes=%s,
                    status = %s
                WHERE batch_id = %s
                """
    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_update, (total_pegawai,
                           json.dumps(notes) if notes else None, status_process, root_batch_id))
            conn.commit()


def save_batch_root_error_logs(error_pegawai_list: list):
    return
    sql_insert = """
                INSERT INTO gaji_batch_root_error_logs(
                    root_batch_id,
                    nipam,
                    nama,
                    notes
                ) VALUES (%s, %s, %s, %s)
                """
    sql_values = []
    for pegawai in error_pegawai_list:
        sql_values.append([pegawai["root_batch_id"],
                           pegawai["nipam"],
                           pegawai["nama"],
                           pegawai["notes"]])

    with POOL.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql_insert, sql_values)
            conn.commit()
