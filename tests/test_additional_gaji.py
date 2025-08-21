from unittest import TestCase

import pandas as pd
import dask.dataframe as dd
from icecream import ic

from core.config import LOGGER
from core.models.gaji_batch_master import fetch_all_gaji_batch_master_by_batch_root_id
from core.models.gaji_batch_master_proses import fetch_gaji_batch_master_proses_by_root_batch_id
from core.process_gaji.additional_gaji import recalculate_gaji


class TestAdditionalGaji(TestCase):
    def test_recalculate_gaji(self):
        root_batch_id = "202501-001"
        master_batch_df = fetch_all_gaji_batch_master_by_batch_root_id(root_batch_id)
        gaji_batch_proses_df = pd.DataFrame(fetch_gaji_batch_master_proses_by_root_batch_id(root_batch_id))

        ddf = dd.from_pandas(master_batch_df, npartitions=4)
        ddf = ddf.map_partitions(lambda part: _applying_dataframe(part, gaji_batch_proses_df),
                                 meta=master_batch_df.dtypes.to_dict())
        df = ddf.compute()
        ic(df[["nipam", "total_add_tambahan", "total_add_potongan", "penghasilan_bersih2", "pembulatan2",
               "penghasilan_bersih_final2"]].head().to_dict(orient="records"))

        # recalculate_gaji(master_batch_df, gaji_batch_proses_df)


def _calculate_add(row: pd.Series, gaji_batch_proses_df: pd.DataFrame):
    return row


def _applying_dataframe(partition: pd.DataFrame, gaji_batch_proses_df: pd.DataFrame):
    partition = partition.apply(lambda row: recalculate_gaji(row, gaji_batch_proses_df), axis=1)
    return partition
    # return partition.apply(lambda row: recalculate_gaji(row, process_data_df), axis=1)


def _recalculate_gaji(row: pd.Series, gaji_batch_proses_df: pd.DataFrame):
    mask = gaji_batch_proses_df["batch_master_id"].eq(row["id"])
    gaji_batch_proses_df = gaji_batch_proses_df[mask].reset_index(drop=True)
    LOGGER.info(gaji_batch_proses_df["id"].size)
    return row
