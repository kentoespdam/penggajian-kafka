from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell
from openpyxl.styles import Font, Alignment, Border, Side

other_option = {
    "start_row": None,
    "start_column": None,
    "end_row": None,
    "end_column": None
}

def cell_builder(worksheet: Worksheet, row_num: int, column_num: int, content: str, border: str = None) -> Cell:
    """Build a cell in the given worksheet at the given row_num and column_num.

    :param Worksheet worksheet: The worksheet to build the cell in
    :param int row_num: The row number to build the cell at
    :param int column_num: The column number to build the cell at
    :param str content: The content of the cell
    :param str border: The border of the cell, defaults to None
    :return Cell: The built cell
    """
    cell = worksheet.cell(row=row_num, column=column_num)
    cell.value = content
    if border:
        border_chars = list(border.lower())
        border_list = []
        if "t" in border_chars:
            border_list.append(("top", Side(style="thin")))
        if "b" in border_chars:
            border_list.append(("bottom", Side(style="thin")))
        if "l" in border_chars:
            border_list.append(("left", Side(style="thin")))
        if "r" in border_chars:
            border_list.append(("right", Side(style="thin")))
        cell.border = Border(**dict(border_list))

    return cell
