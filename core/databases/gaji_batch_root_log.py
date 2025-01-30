from core.config import get_connection_pool
from icecream import ic


def save_batch_root_error_logs(error_pegawai_list: list):
    update_data = [(row["root_batch_id"], row["nipam"],
                    row["nama"], row["notes"]) for row in error_pegawai_list]
    query = """
            INSERT INTO gaji_batch_root_error_logs(
                root_batch_id,
                nipam,
                nama,
                notes
            ) VALUES (%s, %s, %s, %s)
            """
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, update_data)
            conn.commit()
            ic("save_batch_root_error_logs", cursor.rowcount, "affected rows")
