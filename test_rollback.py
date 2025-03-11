from core.databases.gaji_batch_master import rollback_additional_gaji_batch_master_by_batch_root_id, rollback_additional_gaji_batch_master_by_id
from core.databases.gaji_batch_master_proses import rollback_additional_gaji_batch_master_proses
from icecream import ic


def main(batch_master_id: int = None):
    rollback_additional_gaji_batch_master_proses(batch_master_id)
    result = rollback_additional_gaji_batch_master_by_id(
        batch_master_id)
    ic(result)

if __name__ == "__main__":
    main(399)
