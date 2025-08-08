import pandas as pd
from dask.array import isnan

from core.config import LOGGER
from core.enums import PROCESS_GAJI_STATUS, STATUS_PEGAWAI, EProsesGaji, STATUS_KAWIN
from core.models.gaji_batch_master import (
    delete_gaji_batch_master_by_batch_root_id,
    fetch_raw_gaji_master_batch, save_gaji_batch_master,
)
from core.models.gaji_batch_root import (
    fetch_gaji_batch_root_by_id,
    update_status_gaji_batch_root,
)
from core.models.gaji_batch_root_error_logs import (
    delete_batch_root_error_logs_by_root_id,
)
from core.process_gaji.phase1_validation import validate_status_gaji_batch_root, validate_gaji_master


def process_master(batch_root_id: str) -> PROCESS_GAJI_STATUS:
    LOGGER.info(f"Starting phase1: processing gaji master for batch ID {batch_root_id}")
    batch_root_data = fetch_gaji_batch_root_by_id(batch_root_id)

    invalid_status = validate_status_gaji_batch_root(batch_root_data)
    if invalid_status:
        return invalid_status

    LOGGER.info("Updating gaji batch root status to processing")
    update_status_gaji_batch_root(
        batch_root_id, status_process=EProsesGaji.PROSES.value
    )

    cleanup_log_and_batch_data(batch_root_id)

    raw_gaji_master_data = fetch_raw_gaji_master_batch()
    if raw_gaji_master_data.empty:
        LOGGER.error("No data found for processing")
        update_status_gaji_batch_root(
            batch_root_id, status_process=EProsesGaji.FAILED.value
        )
        return PROCESS_GAJI_STATUS.FAILED

    raw_gaji_master_data = cleanup_raw_gaji_master_data(
        raw_gaji_master_data, batch_root_id
    )

    if validate_gaji_master(raw_gaji_master_data) == PROCESS_GAJI_STATUS.FAILED:
        return PROCESS_GAJI_STATUS.FAILED

    try:
        save_gaji_batch_master(raw_gaji_master_data)
    except Exception as e:
        LOGGER.error(e)
        update_status_gaji_batch_root(
            batch_root_id, status_process=EProsesGaji.FAILED.value
        )
        return PROCESS_GAJI_STATUS.FAILED

    LOGGER.info("Gaji master processing completed successfully")
    return PROCESS_GAJI_STATUS.SUCCESS


def cleanup_log_and_batch_data(batch_root_id: str) -> None:
    LOGGER.info("Cleaning up error logs and batch process data")
    delete_batch_root_error_logs_by_root_id(batch_root_id)
    delete_gaji_batch_master_by_batch_root_id(batch_root_id)


def cleanup_raw_gaji_master_data(
        raw_data: pd.DataFrame, batch_root_id: str
) -> pd.DataFrame:
    """Clean up raw gaji master data by adding columns and cleaning golongan_id."""
    result = raw_data.assign(
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
    result = result.assign(
        golongan_id=result.apply(
            lambda row: _cleanup_golongan_id(row),
            axis=1,
        ).astype(int),
        jml_jiwa=result.apply(
            lambda row: _hitung_jumlah_jiwa(row),
            axis=1,
        ).astype(int),
    )
    return result


def _cleanup_golongan_id(data: pd.Series):
    if isnan(data["golongan_id"]):
        return 0
    return (
        1
        if data["status_pegawai"]
           in {STATUS_PEGAWAI.CALON_HONORER.value, STATUS_PEGAWAI.HONORER.value}
        else data["golongan_id"]
    )


def _hitung_jumlah_jiwa(row) -> int:
    is_kawin = 1 if row["status_kawin"] == STATUS_KAWIN.KAWIN.value else 0
    return 1 + row["jml_tanggungan"] + is_kawin
