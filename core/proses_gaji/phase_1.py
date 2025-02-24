from core.config import log_debug, log_info
from core.databases.gaji_batch_master import delete_gaji_batch_master_by_root_batch_id, fetch_raw_gaji_master_batch, save_gaji_batch_master
from core.databases.gaji_batch_root import delete_batch_root_error_logs_by_root_batch_id, fetch_gaji_batch_root_by_batch_id, update_status_gaji_batch_root
from core.databases.gaji_batch_root_log import save_batch_root_error_logs
from core.enums import STATUS_KAWIN, STATUS_PEGAWAI, EProsesGaji
import pandas as pd

def validate_gaji_master(raw_gaji_master: pd.DataFrame) -> tuple[bool, dict]:
    """
    Validate gaji master data
    """
    log_debug(f"validating gaji master")
    errors = []
    summary = {"valid": 0, "error": 0}

    for _, row in raw_gaji_master.iterrows():
        profile_id = row["gaji_profil_id"]
        golongan_id = row["golongan"]
        gaji_pokok = row["gaji_pokok"]

        if profile_id is None:
            log_debug(
                f"missing gaji profil for {row['nipam']} - {row['nama']}")
            summary["error"] += 1
            errors.append({
                "root_batch_id": row["root_batch_id"],
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "Missing gaji profil"
            })
            continue

        if (golongan_id is None and row["level_id"] not in {2, 3, 4} and
                row["status_pegawai"] in {STATUS_PEGAWAI.PEGAWAI.value,
                                          STATUS_PEGAWAI.CAPEG.value}):
            log_debug(f"missing golongan for {row['nipam']} - {row['nama']}")
            summary["error"] += 1
            errors.append({
                "root_batch_id": row["root_batch_id"],
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "Missing golongan"
            })
            continue

        if gaji_pokok is None or gaji_pokok <= 0:
            log_debug(f"invalid gaji pokok for {row['nipam']} - {row['nama']}")
            summary["error"] += 1
            errors.append({
                "root_batch_id": row["root_batch_id"],
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "Invalid gaji pokok"
            })
            continue

        summary["valid"] += 1

    if summary["error"] > 0:
        log_debug(f"proses gaji master failed {summary}")
        update_status_gaji_batch_root(
            root_batch_id=row["root_batch_id"],
            status_process=EProsesGaji.FAILED.value,
            total_pegawai=len(raw_gaji_master),
            notes=summary
        )
        save_batch_root_error_logs(errors)
        return False, summary

    return True, summary


def process_master(root_batch_id: str) -> bool:
    log_info(f"proses gaji master {root_batch_id}")

    # check if root batch id already processed
    gaji_batch_root = fetch_gaji_batch_root_by_batch_id(root_batch_id)
    if gaji_batch_root is None:
        log_debug(f"root batch id {root_batch_id} not found")
        return False
    if gaji_batch_root["status"] == EProsesGaji.PROSES.value:
        log_debug(f"root batch id {root_batch_id} already processed")
        return False

    log_debug("clean up gaji batch master and error logs")
    delete_batch_root_error_logs_by_root_batch_id(root_batch_id)
    delete_gaji_batch_master_by_root_batch_id(root_batch_id)

    update_status_gaji_batch_root(
        root_batch_id=root_batch_id, status_process=EProsesGaji.PROSES.value
    )

    log_debug("fetching raw gaji master")
    raw_salary_data = pd.DataFrame(fetch_raw_gaji_master_batch())

    if raw_salary_data.empty:
        update_status_gaji_batch_root(
            root_batch_id=root_batch_id, status_process=EProsesGaji.FAILED.value
        )
        return False

    log_debug("delete exist gaji batch master by root batch id")

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
    raw_salary_data["golongan_id"] = raw_salary_data.apply(lambda x: 1 if x["status_pegawai"] in {
                                                           STATUS_PEGAWAI.CALON_HONORER.value, STATUS_PEGAWAI.HONORER.value} else x["golongan_id"], axis=1)
    status, summary = validate_gaji_master(raw_salary_data)
    if not status:
        return False

    raw_salary_data["jml_jiwa"] = raw_salary_data.apply(
        lambda x: hitung_jumlah_jiwa(x), axis=1)

    log_debug("saving valid gaji batch master")
    save_gaji_batch_master(raw_salary_data)
    update_status_gaji_batch_root(
        root_batch_id=root_batch_id, 
        status_process=EProsesGaji.PROSES.value,
        total_pegawai=len(raw_salary_data),
        notes=summary
    )
    return True


def hitung_jumlah_jiwa(raw_salary_data: pd.Series) -> int:
    return 1 + raw_salary_data["jml_tanggungan"] + (1 if raw_salary_data["status_kawin"] == STATUS_KAWIN.KAWIN.value else 0)
