from datetime import datetime, timedelta

import pandas as pd

from core.config import LOGGER
from core.models.gaji_batch_master import fetch_gaji_batch_master_by_periode, reset_different_gaji_as_false, \
    update_different_gaji


def compare_with_latest_gaji(root_batch_id: str, current_gaji_df: pd.DataFrame):
    """
    Compare the current gaji batch master data with the latest gaji batch master data.
    If there are any differences, update the 'different_gaji' flag in the current gaji batch master data.
    """
    LOGGER.info(f"Starting phase2: compare with latest gaji for batch ID {root_batch_id}")
    start_time = datetime.now()

    # Get the current period
    current_period = root_batch_id.split("-")[0]
    current_period_date = datetime.strptime(current_period, "%Y%m").date()

    # Get the previous period
    previous_period = (current_period_date - timedelta(days=current_period_date.day)).strftime("%Y%m")

    # Fetch the latest gaji batch master data
    latest_gaji_df = pd.DataFrame(fetch_gaji_batch_master_by_periode(previous_period))
    if latest_gaji_df.empty:
        LOGGER.info("No latest gaji batch master data found\n")
        return

    # Initialize a list to store the different gaji records
    different_gaji_records = []

    # Iterate through the current gaji batch master data and the latest gaji batch master data
    for current_gaji in current_gaji_df.itertuples():
        for latest_gaji in latest_gaji_df.itertuples():
            # If the pegawai ID is the same and the gaji pokok is different, add the record to the list
            if (current_gaji.pegawai_id == latest_gaji.pegawai_id and
                current_gaji.gaji_pokok != latest_gaji.gaji_pokok):
                different_gaji_records.append((current_gaji.batch_root_id, current_gaji.pegawai_id))

    # Reset the 'different_gaji' flag in the current gaji batch master data
    reset_different_gaji_as_false(root_batch_id)

    # If there are any differences, update the 'different_gaji' flag in the current gaji batch master data
    if different_gaji_records:
        LOGGER.error(f"Found {len(different_gaji_records)} pegawai with different gaji")
        update_different_gaji(different_gaji_records)

    end_time = datetime.now()
    LOGGER.info(f"Process gaji finished in {end_time - start_time}")
