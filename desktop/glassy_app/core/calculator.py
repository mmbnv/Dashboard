"""A safe arithmetic expression evaluator for the calculator module.

``eval`` is never used. The expression is parsed with :mod:`ast` and only a
whitelist of numeric operators, functions and constants is allowed, so a
pasted string cannot execute code.
"""

import ast
import math
import re

from .errors import ValidationError

_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}

_ALLOWED_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pow": pow,
}

_ALLOWED_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

# Guards against a paste like 9**9**9 freezing the UI thread.
_MAX_POWER = 1_000_000


def evaluate(expression):
    """Evaluate an arithmetic expression and return a float.

    Raises :class:`ValidationError` with a readable message on any problem.
    """
    text = (expression or "").strip()
    if not text:
        raise ValidationError("Nothing to calculate", field="expression")
    text = (
        text.replace("\u00d7", "*")
        .replace("\u00f7", "/")
        .replace("\u2212", "-")
    )
    # A comma is a decimal separator in Russian and German input, but it is
    # also an argument separator in min(3, 1). Only treat it as a decimal point
    # when it sits between two digits, so "1,5" becomes 1.5 while
    # "min(3, 1)" keeps its comma.
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ValidationError(f"Invalid expression: {exc.msg}", field="expression")
    try:
        return float(_eval_node(tree.body))
    except ZeroDivisionError:
        raise ValidationError("Division by zero", field="expression")
    except (OverflowError, ValueError) as exc:
        raise ValidationError(f"Could not compute: {exc}", field="expression")


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValidationError("Only numbers are allowed", field="expression")
        return node.value

    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise ValidationError("Unsupported operator", field="expression")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and (abs(left) > 1 and abs(right) > _MAX_POWER):
            raise ValidationError("Exponent is too large", field="expression")
        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_UNARYOPS.get(type(node.op))
        if op is None:
            raise ValidationError("Unsupported operator", field="expression")
        return op(_eval_node(node.operand))

    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_NAMES:
            return _ALLOWED_NAMES[node.id]
        raise ValidationError(f"Unknown name: {node.id}", field="expression")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValidationError("Unsupported function call", field="expression")
        func = _ALLOWED_FUNCS.get(node.func.id)
        if func is None:
            raise ValidationError(
                f"Unknown function: {node.func.id}", field="expression"
            )
        if node.keywords:
            raise ValidationError("Keyword arguments are not supported")
        return func(*[_eval_node(arg) for arg in node.args])

    if isinstance(node, (ast.Tuple, ast.List)):
        return [_eval_node(el) for el in node.elts]

    raise ValidationError("Unsupported expression", field="expression")


def format_result(value):
    """Render a float result the way a person expects to read it."""
    if value is None:
        return ""
    if float(value).is_integer() and abs(value) < 1e15:
        return f"{int(value):,}".replace(",", "\u00a0")
    return f"{value:,.10g}".replace(",", "\u00a0")


# -- percentage helpers used by the calculator page ----------------------
def percent_of(base, percent):
    return base * percent / 100.0


def percent_change(old, new):
    if old == 0:
        return float("inf") if new else 0.0
    return (new - old) / abs(old) * 100.0


def loan_payment(principal, annual_rate, months):
    """Annuity payment for a loan. Returns (payment, total, overpay)."""
    if months <= 0:
        raise ValidationError("Term must be at least one month", field="months")
    if annual_rate == 0:
        payment = principal / months
    else:
        monthly = annual_rate / 100.0 / 12.0
        payment = principal * monthly / (1 - (1 + monthly) ** (-months))
    total = payment * months
    return payment, total, total - principal
