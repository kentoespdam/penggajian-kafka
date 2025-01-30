from core.config import log_error
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
    # phase1=process_master(root_batch_id)
    # if not phase1:
    #     log_error("proses master failed")
    #     return
    
    """ 
        Phase 2:
        - fetch gaji batch master
        - calculate komponen gaji
        - update gaji batch master 
    """
    phase2=calculate_gaji_detail(root_batch_id)
    if not phase2:
        log_error("proses detail failed")
        return

    ic("proses master success")

if __name__ == "__main__":
    main("202401-001")
