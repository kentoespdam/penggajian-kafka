from core.config import get_connection_pool


def delete_batch_root_error_logs_by_root_id(root_batch_id: str):
    query = "DELETE FROM gaji_batch_root_error_logs WHERE root_batch_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (root_batch_id,))
            conn.commit()


def save_batch_root_error_logs(errors: list):
    """Save errors encountered during gaji batch processes into databases"""

    data = [
        (row["root_batch_id"], row["nipam"], row["nama"], row["notes"])
        for row in errors
    ]

    query = "INSERT INTO gaji_batch_root_error_logs (root_batch_id, nipam, nama, notes) VALUES (%s, %s, %s, %s)"

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, data)
            conn.commit()
