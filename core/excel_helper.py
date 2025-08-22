from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.worksheet.worksheet import Worksheet

other_option = {
    "start_row": None,
    "start_column": None,
    "end_row": None,
    "end_column": None,
}

NUMBER_FORMAT = "#,##0"

# Border constants
BORDER_THIN = {"top": "thin", "left": "thin", "right": "thin", "bottom": "thin"}
BORDER_LR_THIN = {"left": "thin", "right": "thin"}
BORDER_TLR_THIN = {"top": "thin", "left": "thin", "right": "thin"}
BORDER_LRB_THIN = {"bottom": "thin", "left": "thin", "right": "thin"}


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


def copy_sheet_from_template(workbook: Workbook, template_name: str, new_title: str) -> Worksheet:
    """
    Copy a template sheet by name and retitle the copy.
    """
    workbook.active = workbook[template_name]
    ws = workbook.copy_worksheet(workbook.active)
    ws.title = new_title
    return ws


def auto_width(worksheet: Worksheet, curr_cell, content: str, min_width: int = 10, padding: int = 4) -> None:
    max_length = max(len(content), min_width)
    worksheet.column_dimensions[curr_cell.column_letter].width = max_length + padding
