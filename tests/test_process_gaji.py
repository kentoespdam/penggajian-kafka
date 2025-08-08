import logging

logging.basicConfig(level='DEBUG',
                    format='%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)', encoding='utf-8')


class TestProcessGaji:
    def test_phase1(self):
        from core.enums import PROCESS_GAJI_STATUS
        from core.process_gaji.phase1 import process_master
        from core.config import LOGGER
        result = process_master("202501-001")
        LOGGER.debug(result)
        assert result == PROCESS_GAJI_STATUS.SUCCESS

    def test_phase2(self):
        from core.enums import PROCESS_GAJI_STATUS
        from core.process_gaji.phase2 import calculate_gaji_detail
        from core.config import LOGGER
        result = calculate_gaji_detail("202501-001")
        LOGGER.debug(result)
        assert result == PROCESS_GAJI_STATUS.SUCCESS
