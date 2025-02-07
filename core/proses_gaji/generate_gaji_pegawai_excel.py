import datetime
from icecream import ic
from core.databases.organisasi import fetch_organisasi_by_level
from core.helper import get_nama_bulan
import pandas as pd


def header_generator():
    sekarang=datetime.datetime.now()
    tahun=sekarang.year
    bulan=sekarang.month
    return [
        "PEMERINTAH KABUPATEN BANYUMAS",
        "PERUSAHAAN DAERAH AIR MINUM TIRTA SATRIA",
        "Jalan Prod. Dr. Suharso No. 52 Purwokerto 53114",
        "Telp. & Fax. (0281) - 632324",
        "<<separator>>",
        "Daftar: Gaji Pegawai",
        # "Bulan: {} {}".format(NAMA_BULAN[bulan].value)
    ]

def main():
    organisasi_list=pd.DataFrame(fetch_organisasi_by_level([2, 3, 4]))
    ic(get_nama_bulan(1))
    pass


if __name__ == "__main__":
    main()
