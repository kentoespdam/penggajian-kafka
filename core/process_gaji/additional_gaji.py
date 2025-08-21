from math import ceil
import pandas as pd
from core.config import get_connection_pool, LOGGER
from core.enums import JENIS_GAJI

# Column name constants
COL_BATCH_MASTER_ID = "batch_master_id"
COL_ID = "id"
COL_JENIS_GAJI = "jenis_gaji"
COL_KODE = "kode"
COL_NILAI = "nilai"

# Output columns
COL_TOTAL_ADD_TAMBAHAN = "total_add_tambahan"
COL_TOTAL_ADD_POTONGAN = "total_add_potongan"
COL_PENGHASILAN_BERSIH2 = "penghasilan_bersih2"
COL_PEMBULATAN2 = "pembulatan2"
COL_PENGHASILAN_BERSIH_FINAL2 = "penghasilan_bersih_final2"

# SQL constants
SQL_UPDATE_ADDITIONAL = """
    UPDATE gaji_batch_master
    SET total_add_tambahan        = %s,
        total_add_potongan        = %s,
        penghasilan_bersih2       = %s,
        pembulatan2               = %s,
        penghasilan_bersih_final2 = %s
    WHERE id = %s
"""


def _compute_net_income(total_pemasukan: float, total_potongan: float) -> float:
    """Compute net income (penghasilan bersih)."""
    return total_pemasukan - total_potongan


def _compute_pembulatan_to_next_100(amount: float) -> float:
    """
    Compute the rounding up adjustment to reach the next hundred.
    Example: amount=123 -> pembulatan= (200-123)=77
    """
    return round((ceil(amount / 100) * 100) - amount, 2)


def _sum_by_filters(df: pd.DataFrame, *, jenis: str | None = None, kode_prefix: str | None = None) -> float:
    """Generic summation helper on COL_NILAI with optional filters."""
    mask = pd.Series([True] * len(df))
    if jenis is not None:
        mask &= df[COL_JENIS_GAJI] == jenis
    if kode_prefix is not None:
        mask &= df[COL_KODE].str.startswith(kode_prefix)
    filtered = df[mask].copy()
    return 0.0 if filtered.empty else float(filtered[COL_NILAI].sum())


def recalculate_gaji(master_batch_df: pd.Series, gaji_batch_proses_df: pd.DataFrame):
    """
    Recalculate additional amounts and net income-related fields for a given master batch.
    Mutates and returns master_batch with computed columns.
    """
    # Filter only rows related to the provided master batch
    mask = gaji_batch_proses_df[COL_BATCH_MASTER_ID].eq(master_batch_df[COL_ID])
    gaji_batch_proses_for_batch_df = gaji_batch_proses_df[mask].reset_index(drop=True)

    # Additional components (ADD_) by type
    add_tambahan = _sum_by_filters(gaji_batch_proses_for_batch_df, jenis=JENIS_GAJI.PEMASUKAN.value, kode_prefix="ADD_")
    add_potongan = _sum_by_filters(gaji_batch_proses_for_batch_df, jenis=JENIS_GAJI.POTONGAN.value, kode_prefix="ADD_")

    # Totals by type
    total_pemasukan = _sum_by_filters(gaji_batch_proses_for_batch_df, jenis=JENIS_GAJI.PEMASUKAN.value)
    total_potongan = _sum_by_filters(gaji_batch_proses_for_batch_df, jenis=JENIS_GAJI.POTONGAN.value)

    # Net income and rounding
    penghasilan_bersih = _compute_net_income(total_pemasukan, total_potongan)
    pembulatan = _compute_pembulatan_to_next_100(penghasilan_bersih)
    penghasilan_bersih_final = penghasilan_bersih + pembulatan

    # Assign results
    master_batch_df[COL_TOTAL_ADD_TAMBAHAN] = add_tambahan
    master_batch_df[COL_TOTAL_ADD_POTONGAN] = add_potongan
    master_batch_df[COL_PENGHASILAN_BERSIH2] = penghasilan_bersih
    master_batch_df[COL_PEMBULATAN2] = pembulatan
    master_batch_df[COL_PENGHASILAN_BERSIH_FINAL2] = penghasilan_bersih_final
    return master_batch_df


def _filter_gbp_by_jenis_gaji(df: pd.DataFrame, jenis_gaji: str) -> float:
    """Sum nilai by jenis_gaji."""
    return _sum_by_filters(df, jenis=jenis_gaji)


def _filter_add_gbp(df: pd.DataFrame, jenis_gaji: str) -> float:
    """Sum nilai for additional (ADD_) entries by jenis_gaji."""
    return _sum_by_filters(df, jenis=jenis_gaji, kode_prefix="ADD_")


def update_additional_gaji(df: pd.Series) -> None:
    """
    Persist additional and net income fields for each batch row in df.
    Expects columns:
      - total_add_tambahan, total_add_potongan, penghasilan_bersih2, pembulatan2, penghasilan_bersih_final2, id
    """
    data = [
        (
            row.total_add_tambahan,
            row.total_add_potongan,
            row.penghasilan_bersih2,
            row.pembulatan2,
            row.penghasilan_bersih_final2,
            row.id,
        )
        for row in df.itertuples(index=False)
    ]

    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(SQL_UPDATE_ADDITIONAL, data)
        conn.commit()
