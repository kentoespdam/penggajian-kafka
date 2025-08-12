import sys
from datetime import datetime

import dask.dataframe as dd
import pandas as pd

from core.config import LOGGER
from core.enums import PROCESS_GAJI_STATUS, EProsesGaji
from core.helpers import cleanup_is_boolean
from core.models.gaji_batch_master import fetch_gaji_batch_master_data_by_batch_root_id, update_gaji_batch_master
from core.models.gaji_batch_master_proses import delete_gaji_batch_master_proses_by_batch_master_id_list, \
    save_gaji_batch_master_proses
from core.models.gaji_batch_potongan_tkk import fetch_gaji_batch_potongan_tkk
from core.models.gaji_batch_root import update_status_gaji_batch_root
from core.models.gaji_komponen import fetch_gaji_komponen
from core.models.gaji_parameter import fetch_parameter_setting
from core.models.gaji_pendapatan_non_pajak import fetch_gaji_pendapatan_non_pajak
from core.models.gaji_potongan_tkk import fetch_gaji_potongan_tkk
from core.models.gaji_tunjangan import fetch_tunjangan
from core.models.rumah_dinas import fetch_rumah_dinas
from core.process_gaji.phase2_calculate import _calculate_nilai_formula, _cleanup_nilai_referensi_komponen_gaji, \
    _applying_dataframe
from core.process_gaji.phase2_compare import compare_with_latest_gaji
from core.process_gaji.phase2_helper import _replace_formula_to_variable


def calculate_gaji_detail(root_batch_id: str) -> PROCESS_GAJI_STATUS:
    start_time = datetime.now()
    LOGGER.info(f"Starting phase2: calculate gaji detail for batch ID {root_batch_id}")
    gbm_df = fetch_gaji_batch_master_data_by_batch_root_id(root_batch_id)
    if gbm_df.empty:
        LOGGER.error("No data found for processing")
        update_status_gaji_batch_root(
            root_batch_id, status_process=EProsesGaji.FAILED.value
        )
        return PROCESS_GAJI_STATUS.FAILED

    gbm_ddf = dd.from_pandas(gbm_df, npartitions=2)
    gbm_ddf["is_askes"] = gbm_ddf["is_askes"].map(cleanup_is_boolean, meta=("is_askes", "bool"))
    gbm_df = gbm_ddf.compute()

    gbm_df = process_gaji_komponen_detail(root_batch_id, gbm_df)
    if gbm_df.empty:
        return PROCESS_GAJI_STATUS.FAILED

    gbm_df["penghasilan_kotor2"] = 0
    gbm_df["penghasilan_bersih2"] = 0
    gbm_df["pembulatan2"] = 0
    gbm_df["penghasilan_bersih_final2"] = 0

    compare_with_latest_gaji(root_batch_id, gbm_df)

    try:
        LOGGER.debug("update gaji batch master")
        update_gaji_batch_master(gbm_df)

        LOGGER.debug("update gaji batch master proses")
        update_status_gaji_batch_root(
            root_batch_id,
            status_process=EProsesGaji.WAIT_VERIFICATION_PHASE_1.value
        )
    except Exception as e:
        LOGGER.error(e)
        update_status_gaji_batch_root(
            root_batch_id, status_process=EProsesGaji.FAILED.value
        )
        return PROCESS_GAJI_STATUS.FAILED

    end_time = datetime.now()
    LOGGER.info(f"process gaji finished in {end_time - start_time}")
    return PROCESS_GAJI_STATUS.SUCCESS


def process_gaji_komponen_detail(batch_root_id: str, master_df: pd.DataFrame) -> (PROCESS_GAJI_STATUS, pd.DataFrame):
    """
    Process gaji komponen detail for the given batch and master data

    Args:
        batch_root_id (str): The ID of the gaji batch root
        master_df (pd.DataFrame): master data for the gaji batch master

    Returns:
        tuple: A tuple containing the status of the process and the cleaned master data
    """
    process_data_df = generate_gaji_batch_master_process_data(batch_root_id, master_df)

    # Columns that need to be cleaned
    columns_to_clean = [
        "id", "penghasilan_kotor", "total_potongan",
        "penghasilan_bersih", "pembulatan",
        "penghasilan_bersih_final", "pajak"
    ]

    master_data_ddf = dd.from_pandas(master_df, npartitions=4)
    master_data_ddf[columns_to_clean] = master_data_ddf[columns_to_clean].map_partitions(
        lambda partition: _applying_dataframe(partition, process_data_df),
        meta={col: float if col != "id" else int for col in columns_to_clean},
    )

    cleaned_master_df = master_data_ddf.compute()

    # Delete existing data for the current batch
    LOGGER.debug("Delete existing data for the current batch")
    list_master_row_id = process_data_df["batch_master_id"].unique().tolist()
    delete_gaji_batch_master_proses_by_batch_master_id_list(list_master_row_id)

    try:
        # Save the new data
        save_gaji_batch_master_proses(process_data_df)
    except Exception as error:
        LOGGER.error(error)
        # Update the status of the batch root to failed status
        update_status_gaji_batch_root(
            batch_root_id, status_process=EProsesGaji.FAILED.value
        )
        # Return failed status
        return cleaned_master_df.iloc[0:0]

    # Update the status of the batch root to success
    update_status_gaji_batch_root(
        batch_root_id, status_process=EProsesGaji.WAIT_VERIFICATION_PHASE_1.value
    )
    # Return success status
    return cleaned_master_df


def generate_gaji_batch_master_process_data(
        root_batch_id: str, gaji_batch_master_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate data for processing gaji batch master"""
    parameter_df = fetch_parameter_setting()
    max_potongan = {
        "jpn": parameter_df.loc[parameter_df["kode"] == "maksimal_potongan_jpn", "nominal"].iloc[0],
        "askes": parameter_df.loc[parameter_df["kode"] == "maksimal_potongan_askes", "nominal"].iloc[0],
    }

    komponen_gaji_df = fetch_gaji_komponen()
    komponen_gaji_ddf = dd.from_pandas(komponen_gaji_df, npartitions=4)
    komponen_gaji_ddf["is_reference"] = komponen_gaji_ddf["is_reference"].map(cleanup_is_boolean,
                                                                              meta=("is_reference", "bool"))
    komponen_gaji_df = komponen_gaji_ddf.compute()

    tunjangan_df = fetch_tunjangan()
    rumah_dinas_df = fetch_rumah_dinas()
    potongan_tkk_df = fetch_gaji_potongan_tkk()
    gaji_batch_potongan_tkk_df = fetch_gaji_batch_potongan_tkk(root_batch_id)
    pendapatan_non_pajak_df = fetch_gaji_pendapatan_non_pajak()

    return generate_result_gaji_batch_master(
        gaji_batch_master_df,
        komponen_gaji_df,
        tunjangan_df,
        rumah_dinas_df,
        potongan_tkk_df,
        gaji_batch_potongan_tkk_df,
        pendapatan_non_pajak_df,
        max_potongan,
    )


def generate_result_gaji_batch_master(
        batch_master_df: pd.DataFrame,
        components_df: pd.DataFrame,
        allowances_df: pd.DataFrame,
        housing_df: pd.DataFrame,
        deductions_df: pd.DataFrame,
        batch_deductions_df: pd.DataFrame,
        non_tax_income_df: pd.DataFrame,
        max_deductions: dict
) -> pd.DataFrame:
    final_df = pd.DataFrame()
    spinner = ['|', '/', '-', '\\']
    total_rows = batch_master_df["id"].size - 1
    for index, master_row in batch_master_df.iterrows():
        # if master_row["nipam"] != "900800456":
        #     continue

        LOGGER.debug(f'Processing salary component details for {master_row["nipam"]} - {master_row["nama"]}')

        profile_components_df = components_df.query(
            'profil_gaji_id==@master_row["gaji_profil_id"]'
        ).reset_index(drop=True)

        profile_components_ddf = dd.from_pandas(profile_components_df, npartitions=1)

        profile_components_ddf = profile_components_ddf.assign(
            batch_master_id=master_row["id"],
            nilai=profile_components_ddf["nilai"].where(
                ~profile_components_ddf["is_reference"],
                _cleanup_nilai_referensi_komponen_gaji(
                    profile_components_ddf["kode"], master_row,
                    allowances_df, housing_df,
                    deductions_df, batch_deductions_df,
                    non_tax_income_df
                )
            )
        )

        profile_components_ddf["nilai_formula"] = profile_components_ddf["formula"].map(
            _replace_formula_to_variable,
            meta=("nilai_formula", "string")
        )

        profile_components_df = profile_components_ddf.compute()

        profile_components_df = _calculate_nilai_formula(profile_components_df, master_row, max_deductions)

        final_df = pd.concat([final_df, profile_components_df])

        progress = (index / total_rows) * 100  # noqa
        sys.stdout.write(f'\rCalculating Data {spinner[index % len(spinner)]} : {progress:.2f}%')  # noqa
        sys.stdout.flush()

    return final_df
