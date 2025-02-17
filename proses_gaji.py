import datetime
from core.config import log_error, log_info
from core.proses_gaji import himpunan_gaji_excel, potongan_gaji_excel
from core.proses_gaji.phase_1 import process_master
from icecream import ic

from core.proses_gaji.phase_2 import calculate_gaji_detail

def main(root_batch_id: str):
    """ 
        Phase 1:
        - generate raw gaji batch master
        - validate raw gaji batch master
        - save raw gaji batch master 
    """
    start_time=datetime.datetime.now()
    phase1=process_master(root_batch_id)
    if not phase1:
        log_error("proses master failed")
        return
    log_info(f"Phase 1 success in {datetime.datetime.now() - start_time}\n")

    """ 
        Phase 2:
        - fetch gaji batch master
        - calculate komponen gaji
        - update gaji batch master 
    """
    start_time=datetime.datetime.now()
    phase2=calculate_gaji_detail(root_batch_id)
    if not phase2:
        log_error("proses detail failed")
        return
    log_info(f"Phase 2 success in {datetime.datetime.now() - start_time}\n")

    """ 
        Phase 3:
        - generate himpunan gaji excel
    """
    start_time=datetime.datetime.now()
    himpunan_gaji_excel.build(root_batch_id)
    log_info(f"Phase 3 success in {datetime.datetime.now() - start_time}\n")

    """ 
        Phase 4:
        - generate potongan gaji excel
    """
    start_time=datetime.datetime.now()
    potongan_gaji_excel.build(root_batch_id)
    log_info(f"Phase 4 success in {datetime.datetime.now() - start_time}\n")

if __name__ == "__main__":
    main("202402-001")
