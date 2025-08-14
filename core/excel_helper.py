from datetime import datetime
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell
from openpyxl.styles import Font, Alignment, Border, Side

other_option = {
    "start_row": None,
    "start_column": None,
    "end_row": None,
    "end_column": None,
}

NUMBER_FORMAT = "#,##0"

def cell_builder(
    worksheet: Worksheet,
    row_num: int,
    column_num: int,
    content: str | float | int | datetime,
    font_bold: bool = False,
    border: dict | None = None,
    vertical_alignment: str | None = None,
    horizontal_alignment: str | None = None,
):
    """Build a cell in the given worksheet at the given row number and column number.

    Args:
    - worksheet: The worksheet to build the cell in
    - row_num: The row number to build the cell at
    - column_num: The column number to build the cell at
    - content: The content of the cell
    - is_bold: Whether the cell should be bold, defaults to False
    - border: The border of the cell, defaults to None
    - vertical_alignment: The vertical alignment of the cell, defaults to None
    - horizontal_alignment: The horizontal alignment of the cell, defaults to None

    Returns:
    - Cell: The built cell
    """
    cell = worksheet.cell(row=row_num, column=column_num)
    cell.value = content

    # if border:
    #     border_chars = list(border.lower())
    #     border_list = []
    #     if "t" in border_chars:
    #         border_list.append(("top", Side(style="thin")))
    #     if "b" in border_chars:
    #         border_list.append(("bottom", Side(style="thin")))
    #     if "l" in border_chars:
    #         border_list.append(("left", Side(style="thin")))
    #     if "r" in border_chars:
    #         border_list.append(("right", Side(style="thin")))
    #     cell.border = Border(**dict(border_list))
    if border:
        style_top = Side(border["top"]) if "top" in border else None
        style_bottom = Side(border["bottom"]) if "bottom" in border else None
        style_left = Side(border["left"]) if "left" in border else None
        style_right = Side(border["right"]) if "right" in border else None
        cell.border = Border(
            top=style_top, bottom=style_bottom, left=style_left, right=style_right
        )

    cell.alignment = Alignment(
        horizontal=horizontal_alignment,
        vertical=vertical_alignment,
    )

    if font_bold:
        cell.font = Font(bold=True)

    return cell
