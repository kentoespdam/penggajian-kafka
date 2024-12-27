import pandas as pd
from sqlalchemy import text

from config import ENGINE
from enums import HUBUNGAN_KELUARGA, STATUS_KAWIN, STATUS_KERJA, STATUS_PENDIDIKAN


def update_tanggungan(pegawai_id: int = None) -> None:
    """Update tanggungan status for each pegawai based on their anak's status."""
    sql = """
        SELECT
            pk.id,
            pk.biodata_id,
            pk.tanggal_lahir,
            pk.status_kawin,
            pk.status_pendidikan,
            TIMESTAMPDIFF(
                YEAR,
                pk.tanggal_lahir,
                CURRENT_DATE
            ) AS umur,
            IF(
                CURRENT_DATE > DATE_ADD(pk.tanggal_lahir, INTERVAL 21 YEAR),
                TRUE,
                FALSE
            ) AS gt21,
            IF(
                CURRENT_DATE > DATE_ADD(pk.tanggal_lahir, INTERVAL 26 YEAR),
                TRUE,
                FALSE
            ) AS gt26
        FROM
            profil_keluarga pk
            INNER JOIN pegawai p
                ON pk.biodata_id = p.biodata_id
                AND p.is_deleted = FALSE
                AND p.status_kerja IN (%s, %s)
        WHERE
            pk.is_deleted = FALSE
            AND pk.hubungan_keluarga = %s
            AND tanggungan = TRUE
        """
    params = [
        STATUS_KERJA.KARYAWAN_AKTIF.value,
        STATUS_KERJA.DIRUMAHKAN.value,
        HUBUNGAN_KELUARGA.ANAK.value,
    ]
    if pegawai_id:
        sql += " AND p.id = %s"
        params.append(pegawai_id)

    df = pd.read_sql(sql, con=ENGINE, params=tuple(params))

    for index, row in df.iterrows():
        status_kawin = row["status_kawin"]
        gt21 = row["gt21"]
        gt26 = row["gt26"]
        status_pendidikan = row["status_pendidikan"]

        if (
            status_kawin == STATUS_KAWIN.KAWIN.value
            or gt26 == 1
            or (
                gt21 == 1
                and status_pendidikan == STATUS_PENDIDIKAN.SELESAI_SEKOLAH.value
            )
        ):
            # Release Tanggungan
            with ENGINE.begin() as conn:
                sql_update = text(
                    """
                    UPDATE profil_keluarga
                    SET tanggungan = FALSE
                    WHERE id = :id
                    """
                )
                conn.execute(sql_update, parameters={"id": row["id"]})
            df.drop(index, inplace=True)

    df_grouped = df.groupby("biodata_id").agg({"id": "count"}).reset_index()
    df_grouped = df_grouped.rename(columns={"id": "jml_tanggunan"})

    for index, row in df_grouped.iterrows():
        with ENGINE.begin() as conn:
            sql_update = text(
                """
                UPDATE pegawai
                SET jml_tanggungan = :jml_tanggunan
                WHERE biodata_id = :biodata_id
                """
            )
            conn.execute(
                sql_update,
                parameters={
                    "jml_tanggunan": row["jml_tanggunan"],
                    "biodata_id": row["biodata_id"],
                },
            )


if __name__ == "__main__":
    update_tanggungan()
