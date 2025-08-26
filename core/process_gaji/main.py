from datetime import datetime

from core.config import LOGGER
from core.enums import PROCESS_GAJI_STATUS
from core.process_gaji.phase1 import process_master
from core.process_gaji.phase2 import calculate_gaji_detail
from core.process_gaji.phase3 import build_himpunan_gaji
from core.process_gaji.phase4 import build_potongan_gaji


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

    LOGGER.info("\n=========================================================\n")
    # phase 3
    build_himpunan_gaji(batch_root_id)

    LOGGER.info("\n=========================================================\n")
    # phase 4
    build_potongan_gaji(batch_root_id)