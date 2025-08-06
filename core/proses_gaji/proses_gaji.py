import datetime

from icecream import ic

from core.config import log_error, log_info
from core.databases.gaji_batch_root import update_status_gaji_batch_root
from core.enums import EProsesGaji
from core.proses_gaji import himpunan_gaji_excel, potongan_gaji_excel
from core.proses_gaji.phase_1 import process_master
from core.proses_gaji.phase_2 import calculate_gaji_detail


def execute(batch_root_id: str):
    """ 
        Phase 1:
        - generate raw gaji batch master
        - validate raw gaji batch master
        - save raw gaji batch master 
    """
    start_time = datetime.datetime.now()
    try:
        phase1 = process_master(batch_root_id)
    except Exception as e:
        update_status_gaji_batch_root(
            batch_root_id, status_process=EProsesGaji.FAILED.value)
        ic("phase 1 failed")
        ic(e)
        return
    # if not phase1:
    #     log_error("proses master failed")
    #     return
    # log_info(f"Phase 1 success in {datetime.datetime.now() - start_time}\n")

    """ 
        Phase 2:
        - fetch gaji batch master
        - calculate komponen gaji
        - update gaji batch master 
    """
    start_time = datetime.datetime.now()
    try:
        phase2 = calculate_gaji_detail(batch_root_id)
    except Exception as e:
        update_status_gaji_batch_root(
            batch_root_id, status_process=EProsesGaji.FAILED.value)
        ic("phase 2 failed")
        ic(e)
        return
    # if not phase2:
    #     log_error("proses detail failed")
    #     return
    # log_info(f"Phase 2 success in {datetime.datetime.now() - start_time}\n")

    """ 
        Phase 3:
        - generate himpunan gaji excel
    """
    try:
        start_time = datetime.datetime.now()
        himpunan_gaji_excel.build(batch_root_id)
        log_info(
            f"Phase 3 success in {datetime.datetime.now() - start_time}\n")
    except Exception as e:
        ic(e)

    """ 
        Phase 4:
        - generate potongan gaji excel
    """
    try:
        start_time = datetime.datetime.now()
        potongan_gaji_excel.build(batch_root_id)
        log_info(
            f"Phase 4 success in {datetime.datetime.now() - start_time}\n")
    except Exception as e:
        ic(e)

    log_info(f"Proses Gaji Done\n")
