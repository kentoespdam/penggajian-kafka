from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell
from openpyxl.styles import Font, Alignment, Border, Side
from icecream import ic

merge_option = {
    "start_row": None,
    "start_column": None,
    "end_row": None,
    "end_column": None
}


def header_builder(worksheet: Worksheet, row_num: int, content: str, h_aligment: str = "center", v_aligment: str = "top") -> Cell:
    """
    Build a header cell in the given worksheet at the given row_num

    :param Worksheet worksheet: The worksheet to build the header cell in
    :param int row_num: The row number to build the header cell at
    :param str content: The content of the header cell
    :param str alignment: The alignment of the header cell, defaults to "center"
    :return Cell: The built header cell
    """
    cell = worksheet.cell(row=row_num, column=1, value=content)
    cell.alignment = Alignment(horizontal=h_aligment, vertical=v_aligment)
    cell.font = Font(bold=True)

    if content == "<<separator>>":
        cell.border = Border(top=Side(style='double'))
        cell.value = ""
    elif content == "<<spacing>>":
        cell.value = ""

    return cell

def cell_builder(worksheet: Worksheet, row_num: int, column_num: int, content: str, h_aligment: str = "center", v_aligment: str = "top", **merge_option) -> Cell:
    """
    Build a cell in the given worksheet at the given row_num and column_num

    :param Worksheet worksheet: The worksheet to build the cell in
    :param int row_num: The row number to build the cell at
    :param int column_num: The column number to build the cell at
    :param str content: The content of the cell
    :param str alignment: The alignment of the cell, defaults to "center"
    :return Cell: The built cell
    """
    cell = worksheet.cell(row=row_num, column=column_num, value=content)
    cell.alignment = Alignment(horizontal=h_aligment, vertical=v_aligment)
    if merge_option:
        merge_option=merge_option["merge_option"]
        ic(merge_option)
        worksheet.merge_cells(start_row=merge_option["start_row"], start_column=merge_option["start_column"], end_row=merge_option["end_row"], end_column=merge_option["end_column"])
    return cell