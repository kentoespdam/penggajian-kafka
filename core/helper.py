import ast
import math
import operator
from icecream import ic


def replace_formula_with_values(formula: str, lookup: dict) -> str:
    # sort lookup by key length to ensure longest match first
    lookup = dict(sorted(lookup.items(), key=lambda item: len(item[0]), reverse=True))
    try:
        for code, value in lookup.items():
            formula = formula.replace(code, str(value))
        return formula
    except Exception as error:
        ic("Error evaluating formula:", error)
        return None


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
        ast.UAdd: operator.pos, # Unary plus (+3)
        ast.USub: operator.neg, # Unary minus (-3)
    }

    allowed_functions={
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
                return func(*args)
        elif isinstance(node, ast.Constant):  # Number
            return node.n
        elif isinstance(node, ast.Expression):
            return eval_node(node.body)
        else:
            raise ValueError(f"Unsupported operation: {node}")

    tree = ast.parse(expression, mode='eval')
    return eval_node(tree.body)
