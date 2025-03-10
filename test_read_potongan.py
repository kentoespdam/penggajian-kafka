from openpyxl import load_workbook
import pandas as pd
from core.config import get_connection_pool
from core.proses_gaji import additional_gaji
import swifter

def fetch_gaji_batch_master(batch_root_id: str):
    query = "SELECT * FROM gaji_batch_master WHERE batch_root_id = %s"
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (batch_root_id,))
            result = cursor.fetchall()
            return pd.DataFrame(result)


def insert_gaji_batch_master_proses(data):
    query = """
            INSERT INTO gaji_batch_master_proses 
            (jenis_gaji, formula, kode, nama, nilai, nilai_formula, urut, batch_master_id) 
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s)
        """
    with get_connection_pool() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, data)
            conn.commit()


def process_potongan_from_excel(file_path: str, gbm: pd.DataFrame):
    query_data = []
    """Read potongan gaji from Excel file."""
    workbook = load_workbook(file_path, data_only=True)
    exclude_sheet = ["Sheet1"]
    for sheet_name in workbook.sheetnames:
        if sheet_name in exclude_sheet:
            continue
        worksheet = workbook[sheet_name]
        query_data.extend(prosessing_per_sheet(worksheet))

    insert_gaji_batch_master_proses(query_data)
    # recalculate(gbm)
    # gbm["id"].apply(lambda x: additional_gaji.recalculate(x))
    gbm = gbm.swifter.apply(lambda x: additional_gaji.recalculate(x), axis=1)
    additional_gaji.update_additional(gbm)
    workbook.close()


def prosessing_per_sheet(worksheet):
    headers = [cell.value for cell in worksheet[10]]
    headers[0] = "no"
    headers[1] = "nama"
    headers[2] = "nipam"
    headers[3] = "gaji_pokok"
    headers[-2] = "total_potongan"
    headers[-1] = "gaji_bersih"

    data = []
    for row in worksheet.iter_rows(min_row=11, max_row=worksheet.max_row-1, values_only=True):
        if row[0] is None:
            continue
        data.append(row)

    df = pd.DataFrame(data, columns=headers)
    df = df.astype({"nipam": str, "nama": str})
    float_columns = df.columns.difference(["nipam", "nama"])
    df[float_columns] = df[float_columns].astype(float, copy=False)
    return processing_data(gbm, df)


def processing_data(gbm: pd.DataFrame, df: pd.DataFrame):
    """Generate an INSERT query for `gaji_batch_master_proses` table."""
    query_data = []
    for _, row in df.iterrows():
        filtered_gbm = gbm.query(f"nipam == '{row['nipam']}'")
        batch_master_id = filtered_gbm["id"].values[0]
        row["batch_master_id"] = batch_master_id
        datas = generate_insert_query_data(row)
        query_data.extend(datas)
    return query_data


def generate_insert_query_data(row: pd.Series) -> list:
    result = []
    excluded_keys = ["no", "nama", "nipam", "gaji_pokok",
                     "total_potongan", "gaji_bersih", "batch_master_id"]
    for column, value in row.items():
        if pd.isna(value) or value == 0.0 or column in excluded_keys:
            continue
        entry = ("POTONGAN", "", f"ADD_{column}", column,
                 value, value, 99, row["batch_master_id"])
        result.append(entry)
    return result


def recalculate(gaji_batch_master: pd.DataFrame):
    for record in gaji_batch_master.itertuples():
        additional_gaji.recalculate(record.id)


if __name__ == '__main__':
    batch_root_id = "202401-001"
    gbm = fetch_gaji_batch_master(batch_root_id)
    gbm = gbm.astype({"nipam": str})
    process_potongan_from_excel("tmp/temp.xlsx", gbm)
