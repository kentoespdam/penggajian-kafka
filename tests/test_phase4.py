from core.helpers import get_previous_period
from core.models.gaji_batch_master import fetch_daftar_potongan_gaji_by_batch_root_id
from core.models.gaji_batch_master_proses import fetch_additional_gaji_batch_master_proses_by_periode
from core.models.organisasi import fetch_organisasi_by_level
from core.process_gaji.phase4 import build_potongan_gaji


class TestPhase4:
    def test_generate_excel(self):
        batch_root_id = "202502-001"
        periode = batch_root_id.split("-")[0]
        prev_periode = get_previous_period(periode)
        potongan_df = fetch_daftar_potongan_gaji_by_batch_root_id(batch_root_id)
        add_potongan_prev_df = fetch_additional_gaji_batch_master_proses_by_periode(prev_periode)
        organisasi_df = fetch_organisasi_by_level(4)

        assert organisasi_df.empty == False
        assert potongan_df.empty == False
        assert add_potongan_prev_df.empty == False

    def test_build_potongan_gaji(self):
        batch_root_id = "202502-001"
        build_potongan_gaji(batch_root_id)
