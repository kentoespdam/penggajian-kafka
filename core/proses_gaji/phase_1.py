from core.config import log_info
from core.databases.gaji_batch_master import delete_gaji_batch_master_by_batch_root_id, fetch_raw_gaji_master_batch, \
    save_gaji_batch_master
from core.databases.gaji_batch_root import delete_batch_root_error_logs_by_root_id, fetch_gaji_batch_root_by_id, \
    update_status_gaji_batch_root
from core.databases.gaji_batch_root_log import save_batch_root_error_logs
from core.enums import STATUS_KAWIN, STATUS_PEGAWAI, EProsesGaji
import pandas as pd
import swifter  # noqa


def validate_gaji_master(raw_gaji_master: pd.DataFrame) -> tuple[bool, dict]:
    """
    Validate gaji master data.

    Parameters
    ----------
    raw_gaji_master : pd.DataFrame
        Raw gaji master data

    Returns
    -------
    tuple[bool, dict]
        A tuple containing a boolean indicating whether the validation is
        successful and a dictionary containing the summary of validation result.
    """
    log_info(f"validating gaji master")
    errors = []
    summary = {"valid": 0, "error": 0}

    for _, row in raw_gaji_master.iterrows():
        root_batch_id = row["batch_root_id"]
        profile_id = row["gaji_profil_id"]
        golongan_id = row["golongan"]
        gaji_pokok = row["gaji_pokok"]

        # Check if gaji profil is missing
        if profile_id is None:
            log_info(
                f"missing gaji profil for {row['nipam']} - {row['nama']}")
            summary["error"] += 1
            errors.append({
                "batch_root_id": root_batch_id,
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "Missing gaji profil"
            })
            continue

        # Check if golongan is missing
        if (golongan_id is None and row["level_id"] not in {2, 3, 4} and
                row["status_pegawai"] in {STATUS_PEGAWAI.PEGAWAI.value,
                                          STATUS_PEGAWAI.CAPEG.value}):
            log_info(f"missing golongan for {row['nipam']} - {row['nama']}")
            summary["error"] += 1
            errors.append({
                "batch_root_id": root_batch_id,
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "Missing golongan"
            })
            continue

        # Check if gaji pokok is invalid
        if gaji_pokok is None or gaji_pokok <= 0:
            log_info(f"invalid gaji pokok for {row['nipam']} - {row['nama']}")
            summary["error"] += 1
            errors.append({
                "batch_root_id": root_batch_id,
                "nipam": row["nipam"],
                "nama": row["nama"],
                "notes": "Invalid gaji pokok"
            })
            continue

        summary["valid"] += 1

    # If there are errors, update the status of the batch root and save the
    # errors
    if summary["error"] > 0:
        log_info(f"proses gaji master failed {summary}")
        update_status_gaji_batch_root(
            root_batch_id.to_string(),
            status_process=EProsesGaji.FAILED.value,
            total_pegawai=len(raw_gaji_master),
            notes=summary
        )
        save_batch_root_error_logs(errors)
        return False, summary

    # If there are no errors, return True and the summary
    return True, summary


def process_master(batch_root_id: str) -> bool:
    """
    Process a batch of salary master data.

    This function will validate the input data and then save it to the database
    as a batch of salary master data. If any errors occur, the status of the
    batch root is updated and the errors are saved to the database.

    Parameters
    ----------
    batch_root_id : str
        The root batch ID.

    Returns
    -------
    bool
        True if the process is successful, False otherwise.
    """
    log_info(f"proses gaji master {batch_root_id}")

    # check if root batch id already processed
    gaji_batch_root = fetch_gaji_batch_root_by_id(batch_root_id)
    if gaji_batch_root is None:
        log_info(f"root batch id {batch_root_id} not found")
        return False
    if gaji_batch_root["status"] == EProsesGaji.PROSES.value:
        log_info(f"root batch id {batch_root_id} already processed")
        return False

    log_info("clean up gaji batch master and error logs")
    delete_batch_root_error_logs_by_root_id(batch_root_id)
    delete_gaji_batch_master_by_batch_root_id(batch_root_id)

    update_status_gaji_batch_root(
        batch_root_id, status_process=EProsesGaji.PROSES.value)

    log_info("fetching raw gaji master")
    raw_salary_data = pd.DataFrame(fetch_raw_gaji_master_batch())

    if raw_salary_data.empty:
        update_status_gaji_batch_root(
            batch_root_id, status_process=EProsesGaji.FAILED.value
        )
        return False

    log_info("delete exist gaji batch master by root batch id")

    raw_salary_data = raw_salary_data.assign(
        batch_root_id=batch_root_id,
        periode=batch_root_id.split("-")[0],
        penghasilan_kotor=0,
        total_potongan=0,
        total_add_tambahan=0,
        total_add_potongan=0,
        penghasilan_bersih=0,
        pembulatan=0,
        penghasilan_bersih_final=0,
        pajak=0
    )
    raw_salary_data["golongan_id"] = raw_salary_data.swifter.apply(
        lambda x: 1 if x["status_pegawai"] in {
            STATUS_PEGAWAI.CALON_HONORER.value, STATUS_PEGAWAI.HONORER.value
        } else x["golongan_id"],
        axis=1)

    # validate the input data
    status, summary = validate_gaji_master(raw_salary_data)
    if not status:
        return False

    # add the number of jiwa to the dataframe
    raw_salary_data["jml_jiwa"] = raw_salary_data.swifter.apply(
        lambda x: hitung_jumlah_jiwa(x), axis=1)

    log_info("saving valid gaji batch master")
    save_gaji_batch_master(raw_salary_data)
    update_status_gaji_batch_root(
        batch_root_id,
        status_process=EProsesGaji.PROSES.value,
        total_pegawai=len(raw_salary_data),
        notes=summary
    )
    return True


def hitung_jumlah_jiwa(raw_salary_data) -> int:
    """
    Hitung jumlah jiwa dari data pegawai.

    Jumlah jiwa dihitung dari jumlah tanggungan plus 1 (pegawai sendiri) plus 1 lagi jika pegawai sudah kawin.

    Parameters
    ----------
    raw_salary_data : pd.Series
        Data pegawai yang ingin dihitung jumlah jiwanya.

    Returns
    -------
    int
        Jumlah jiwa pegawai.
    """
    jml_tanggungan = raw_salary_data["jml_tanggungan"]
    return 1 + jml_tanggungan + (
        1 if raw_salary_data["status_kawin"] == STATUS_KAWIN.KAWIN.value else 0)
