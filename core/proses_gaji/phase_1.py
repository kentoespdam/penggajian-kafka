import datetime
from core.config import log_error, log_info
from core.databases.gaji_batch_master import delete_gaji_batch_master_by_root_batch_id, fetch_raw_gaji_master_batch, save_gaji_batch_master
from core.databases.gaji_batch_root import delete_batch_root_error_logs_by_root_batch_id, update_status_gaji_batch_root
from core.databases.gaji_batch_root_log import save_batch_root_error_logs
from core.enums import EProsesGaji
import pandas as pd


def validate_master_gaji(raw_salary_data: pd.DataFrame):
    """
    Validasi data gaji master
    """
    log_info("validasi gaji master")
    errors = []
    summary = {"valid": 0, "error": 0}

    for _, row in raw_salary_data.iterrows():
        profile_id = row["gaji_profil_id"]
        golongan_id = row["golongan"]
        gaji_pokok = row["gaji_pokok"]

        if profile_id is None:
            summary["error"] += 1
            errors.append({
                "root_batch_id": row["root_batch_id"],
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "missing gaji profil"
            })
            continue

        if golongan_id is None:
            summary["error"] += 1
            errors.append({
                "root_batch_id": row["root_batch_id"],
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "missing golongan"
            })
            continue

        if gaji_pokok is None or gaji_pokok <= 0:
            summary["error"] += 1
            errors.append({
                "root_batch_id": row["root_batch_id"],
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "invalid gaji pokok"
            })
            continue

        summary["valid"] += 1

    if summary["error"] > 0:
        log_error("validasi gaji master failed")
        update_status_gaji_batch_root(
            root_batch_id=row["root_batch_id"],
            status_process=EProsesGaji.FAILED.value,
            total_pegawai=len(raw_salary_data),
            notes=summary
        )
        save_batch_root_error_logs(errors)
        return False

    return True, summary


def process_master(root_batch_id: str) -> bool:
    log_info(f"proses gaji master {root_batch_id}")

    log_info("clean up gaji batch master and error logs")
    delete_batch_root_error_logs_by_root_batch_id(root_batch_id)
    delete_gaji_batch_master_by_root_batch_id(root_batch_id)

    update_status_gaji_batch_root(
        root_batch_id=root_batch_id, status_process=EProsesGaji.PROSES.value
    )

    log_info("fetching raw gaji master")
    raw_salary_data = pd.DataFrame(fetch_raw_gaji_master_batch())

    if raw_salary_data.empty:
        update_status_gaji_batch_root(
            root_batch_id=root_batch_id, status_process=EProsesGaji.FAILED.value
        )
        return False

    log_info("delete exist gaji batch master by root batch id")

    raw_salary_data = raw_salary_data.assign(
        root_batch_id=root_batch_id,
        periode=root_batch_id.split("-")[0],
        created_by="system",
        updated_by="system",
        penghasilan_kotor=0,
        total_tambahan=0,
        total_potongan=0,
        pembulatan=0,
        penghasilan_bersih=0
    )
    status, summary = validate_master_gaji(raw_salary_data)
    if not status:
        return False

    log_info("saving valid gaji batch master")
    save_gaji_batch_master(raw_salary_data)
    update_status_gaji_batch_root(
        root_batch_id=root_batch_id, status_process=EProsesGaji.WAIT_VERIFICATION_PHASE_1.value,
        total_pegawai=len(raw_salary_data),
        notes=summary
    )
    return True
