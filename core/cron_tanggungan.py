import datetime
import pandas as pd
from core.config import log_debug
from core.enums import STATUS_KAWIN, STATUS_PENDIDIKAN
from core.pegawai import update_pegawai_tanggungan
from core.profil_keluarga import fetch_tanggungan_list, update_tanggungan_status


def calculate_tanggungan(tanggungan_list: pd.DataFrame):
    log_info("calculate tanggungan")
    tanggungan_list.loc[:, "tanggungan"] = ~(
        (tanggungan_list.loc[:, "status_kawin"] == STATUS_KAWIN.KAWIN.value) |
        (tanggungan_list.loc[:, "umur"] > 26) |
        (
            (tanggungan_list.loc[:, "umur"] > 21) &
            (tanggungan_list.loc[:, "status_pendidikan"] ==
             STATUS_PENDIDIKAN.SELESAI_SEKOLAH.value)
        )
    )

    return tanggungan_list


def execute():
    start=datetime.datetime.now()
    log_info("cron tanggungan started")
    # pd.options.mode.copy_on_write = True
    tanggungan_df = pd.DataFrame(fetch_tanggungan_list())
    tanggungan_df = calculate_tanggungan(tanggungan_df)

    update_tanggungan_status(tanggungan_df)
    tanggungan_count_df = (
        tanggungan_df[tanggungan_df["tanggungan"]]
        .groupby("pegawai_id")
        .size()
        .reset_index(name="jumlah_tanggungan")
    )

    update_pegawai_tanggungan(tanggungan_count_df)
    log_info(f"cron tanggungan finished in {datetime.datetime.now() - start}")
