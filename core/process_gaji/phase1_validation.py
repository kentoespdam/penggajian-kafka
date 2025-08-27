import json

import pandas as pd

from core.config import LOGGER
from core.enums import ProcessGajiStatus, EProsesGaji, StatusPegawai
from core.models.gaji_batch_root import (
    update_status_gaji_batch_root,
)
from core.models.gaji_batch_root_error_logs import save_batch_root_error_logs


def validate_status_gaji_batch_root(gbr) -> ProcessGajiStatus | None:
    """
    Validate status gaji batch root, if the status is PROSES (1) then return ProcessGajiStatus.DUPLICATE
    If the gbr is None then return ProcessGajiStatus.FAILED
    :param gbr: pd.DataFrame of gaji batch root
    :return: ProcessGajiStatus
    """
    if gbr is None:
        LOGGER.error("gaji batch root not found")
        return ProcessGajiStatus.FAILED

    elif gbr["status"] == EProsesGaji.FINISHED.value:
        LOGGER.error("gaji batch root already finished")
        return ProcessGajiStatus.FAILED

    elif gbr["status"] == EProsesGaji.PROSES.value:
        LOGGER.error("gaji batch root already processed")
        return ProcessGajiStatus.DUPLICATE

    return None


def validate_gaji_master(gaji_master_df: pd.DataFrame) -> ProcessGajiStatus:
    """
    Validate gaji master data.
    """
    errors = []
    summary = {"valid": 0, "error": 0}

    for _, row in gaji_master_df.iterrows():
        if row["gaji_profil_id"] == 0:
            _append_error(row, errors, "Missing gaji profile id")
            summary["error"] += 1
            continue

        if row["golongan_id"] == 0 and row["level_id"] not in {2, 3, 4} and row["status_pegawai"] in {
            StatusPegawai.PEGAWAI.value, StatusPegawai.CAPEG.value}:
            _append_error(row, errors, "Missing golongan id")
            summary["error"] += 1
            continue

        if row["gaji_pokok"] == 0:
            _append_error(row, errors, "Missing gaji pokok")
            summary["error"] += 1
            continue
        summary["valid"] += 1

    if summary["error"] > 0:
        update_status_gaji_batch_root(
            gaji_master_df["batch_root_id"].iloc[0], status_process=EProsesGaji.FAILED.value,
            total_pegawai=gaji_master_df["pegawai_id"].size,
            notes=json.dumps(summary)
        )
        save_batch_root_error_logs(errors)
        return ProcessGajiStatus.FAILED

    return ProcessGajiStatus.SUCCESS


def _append_error(data: pd.Series, errors: list, notes: str):
    errors.append(
        {
            "root_batch_id": data["batch_root_id"],
            "pegawai_id": data["pegawai_id"],
            "nipam": data["nipam"],
            "nama": data["nama"],
            "notes": notes,
        }
    )


def _collect_missing_gaji_profile_id(df: pd.DataFrame) -> pd.DataFrame:
    """ filter gaji master data that doesn't have gaji profile id"""
    result = df[df["gaji_profil_id"].isna()].reset_index(drop=True)
    return result
