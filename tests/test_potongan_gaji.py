from core.models.gaji_batch_master import fetch_daftar_potongan_gaji_by_batch_root_id
from core.models.organisasi import fetch_organisasi_by_level
from core.process_gaji.phase4 import build_potongan_gaji


class TestHimpunanGaji:
    def test_fetch_organisasi(self):
        organisasi_df = fetch_organisasi_by_level(4)
        # ic(organisasi_df.dtypes)

        assert organisasi_df["id"].size > 0

    def test_fetch_daftar_potongan_gaji(self):
        df = fetch_daftar_potongan_gaji_by_batch_root_id("202501-001")
        # ic(df["penghasilan_bersih"].unique())

        assert df["id"].size > 0

    def test_generate_excel(self):
        build_potongan_gaji("202501-001")
