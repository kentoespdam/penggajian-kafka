import pandas as pd

from core.config import LOGGER

# dataframe from json file
gbm_df = pd.read_json("gaji_batch_master.json", orient="records")
komponen_gaji_df = pd.read_json("dummy_data.json", orient="records")


class TestManipulateNilai:
    def test_manipulate_nilai(self):
        from core.process_gaji.phase2_calculate import _calculate_nilai_formula
        from core.models.gaji_parameter import fetch_parameter_setting

        parameter_setting_df = fetch_parameter_setting()
        maksimal_potongan = {
            "jpn": parameter_setting_df.query("kode == 'maksimal_potongan_jpn'")["nominal"].values[0],
            "askes": parameter_setting_df.query("kode == 'maksimal_potongan_askes'")["nominal"].values[0],
        }
        komponen_df = pd.DataFrame()
        for _, master_row in gbm_df.iterrows():
            komponen_df = komponen_gaji_df.query('profil_gaji_id==@master_row["gaji_profil_id"]').reset_index(drop=True)
            komponen_df = _calculate_nilai_formula(komponen_df, master_row, maksimal_potongan)
        LOGGER.info(komponen_df.to_json("gaji_komponen.json", orient="records"))
        assert 34 == komponen_df["id"].size
