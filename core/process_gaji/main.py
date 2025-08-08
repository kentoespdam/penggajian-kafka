from datetime import datetime

from core.config import LOGGER
from core.enums import PROCESS_GAJI_STATUS
from core.process_gaji.phase1 import process_master
from core.process_gaji.phase2 import calculate_gaji_detail


def execute(batch_root_id: str) -> None:
    """Execute the gaji process."""
    start_time = datetime.now()
    phase1_status = process_master(batch_root_id)

    if phase1_status != PROCESS_GAJI_STATUS.SUCCESS:
        LOGGER.error(f"process gaji status: {phase1_status.value}")
        return

    LOGGER.info("\n=========================================================\n")

    phase2_status = calculate_gaji_detail(batch_root_id)
    if phase2_status != PROCESS_GAJI_STATUS.SUCCESS:
        LOGGER.error(f"calculate gaji detail status: {phase2_status.value}")
        return

    end_time = datetime.now()
    LOGGER.info(f"process gaji finished in {end_time - start_time}")
