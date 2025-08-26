import pandas as pd
from icecream import ic
import dask.dataframe as dd
from core.models.gaji_batch_master import fetch_daftar_gaji_pegawai
from core.process_gaji.phase3 import build_himpunan_gaji

raw_types = {
    "id": int,
    "nipam": str,
    "nama": str,
    "status_pegawai": int,
    "golongan": str,
    "pangkat": str,
    "jml_tanggungan": int,
    "jml_jiwa": int,
    "organisasi_id": int,
    "kode_organisasi": str,
    "nama_organisasi": str,
    "level_id": int,
    "is_different": str
}


class TestHimpunanGaji:
    def test_generate_excel(self):
        build_himpunan_gaji("202501-002")
