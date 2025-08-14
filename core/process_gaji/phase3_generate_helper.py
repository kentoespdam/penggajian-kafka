import itertools

import pandas as pd
from openpyxl.worksheet.worksheet import Worksheet

from core.excel_helper import cell_builder
from core.process_gaji.phase3_helper import get_total_salary, get_component_value


def generate_cell_list(
    worksheet: Worksheet,
    row_num: int,
    col_num: int,
    komponen_gaji_df: pd.DataFrame,
    employee: pd.Series,
    komponen_list: list,
    order_number: int,
    is_first: bool = False,
    is_last: bool = False,
):
    col_counter = itertools.count(start=col_num)

    def build_cell(value: str | int | float, is_number: bool = False):
        cell = cell_builder(
            worksheet,
            row_num,
            next(col_counter),
            value,
            border={
                "left": "thin",
                "right": "thin",
                "bottom": "thin" if is_last else None,
            },
        )
        if is_number:
            cell.number_format = "#,##0"

    for komponen in komponen_list:
        if komponen == "0":
            build_cell(0, True)
        elif komponen == "":
            build_cell("")
        elif komponen == "JUMLAH":
            build_cell(get_total_salary(komponen_gaji_df, employee["id"]), True)
        else:
            build_cell(
                get_component_value(komponen_gaji_df, employee["id"], komponen), True
            )

    if is_first:
        build_cell(str(order_number))
