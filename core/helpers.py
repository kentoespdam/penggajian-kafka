import ast
import math
import operator

import pandas as pd

from core.config import LOGGER


def cleanup_is_boolean(x):
    x.encode("utf-8")
    return True if x == '\x01' else False


def cleanup_empty_string(x):
    if pd.isna(x):
        return ''
    return  x if x is not None else ''

def safe_eval(expression: str):
    # Allowed operators
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitAnd: operator.and_,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.Invert: operator.invert,
        ast.Not: operator.not_,
        ast.UAdd: operator.pos,  # Unary plus (+3)
        ast.USub: operator.neg,  # Unary minus (-3)
    }

    allowed_functions = {
        'ceil': math.ceil
    }

    # return float with 2 digits after decimal
    def eval_node(node):
        if isinstance(node, ast.BinOp):  # Binary operation (e.g., 3 * 72420.0)
            left = eval_node(node.left)
            right = eval_node(node.right)
            operator_func = allowed_operators[type(node.op)]
            return operator_func(left, right)
        elif isinstance(node, ast.UnaryOp):  # Unary operation (e.g., -3)
            operand = eval_node(node.operand)
            operator_func = allowed_operators[type(node.op)]
            return operator_func(operand)
        elif isinstance(node, ast.Call):  # Function call (e.g., ceil(3.14))
            if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                func = allowed_functions[node.func.id]
                args = [eval_node(arg) for arg in node.args]
                return func(*args)  # noqa
            return None
        elif isinstance(node, ast.Constant):  # Number
            return node.n
        elif isinstance(node, ast.Expression):
            return eval_node(node.body)
        else:
            raise ValueError(f"Unsupported operation: {node}")

    tree = ast.parse(expression, mode='eval')
    return eval_node(tree.body)


def get_nama_bulan(bulan: int) -> str:
    list_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November",
        "Desember"
    ]

    return list_bulan[bulan - 1]


def get_nilai_komponen(proses_gaji_df: pd.DataFrame, batch_master_id: pd.Series, kode: str) -> float:
    """Get the nilai of a komponen from proses gaji dataframe."""
    filtered_df = proses_gaji_df[
        (proses_gaji_df["batch_master_id"] == batch_master_id) &
        (proses_gaji_df["kode"] == kode)
        ].reset_index(drop=True)

    return filtered_df["nilai"].values[0] if not filtered_df.empty else 0
