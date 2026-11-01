"""The calculator must be useful and must not execute anything."""

import pytest

from glassy_app.core import calculator
from glassy_app.core.errors import ValidationError


def test_basic_arithmetic():
    assert calculator.evaluate("2+2") == 4
    assert calculator.evaluate("2+2*2") == 6
    assert calculator.evaluate("(2+2)*2") == 8
    assert calculator.evaluate("10/4") == 2.5
    assert calculator.evaluate("2**10") == 1024
    assert calculator.evaluate("-5") == -5


def test_unicode_operators_are_normalised():
    assert calculator.evaluate("6\u00d77") == 42
    assert calculator.evaluate("10\u00f74") == 2.5
    assert calculator.evaluate("10\u22123") == 7
    assert calculator.evaluate("1,5+1,5") == 3


def test_functions_and_constants():
    assert calculator.evaluate("sqrt(16)") == 4
    assert calculator.evaluate("abs(-3)") == 3
    assert calculator.evaluate("round(2.6)") == 3
    assert calculator.evaluate("min(3, 1, 2)") == 1
    assert calculator.evaluate("max(3, 1, 2)") == 3
    assert calculator.evaluate("log(1)") == 0
    assert calculator.evaluate("pi") == pytest.approx(3.14159265, rel=1e-6)
    assert calculator.evaluate("e") == pytest.approx(2.7182818, rel=1e-6)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo pwned')",
        "open('/etc/passwd').read()",
        "eval('1+1')",
        "exec('x=1')",
        "().__class__.__bases__",
        "[x for x in range(3)]",
        "lambda: 1",
        "x = 5",
        "print(1)",
    ],
)
def test_code_execution_is_refused(expression):
    with pytest.raises(ValidationError):
        calculator.evaluate(expression)


def test_errors_are_readable():
    with pytest.raises(ValidationError):
        calculator.evaluate("")
    with pytest.raises(ValidationError):
        calculator.evaluate("1/0")
    with pytest.raises(ValidationError):
        calculator.evaluate("1+")
    with pytest.raises(ValidationError):
        calculator.evaluate("unknownname")


def test_huge_exponent_is_refused():
    with pytest.raises(ValidationError):
        calculator.evaluate("9**999999999")


def test_formatting():
    assert calculator.format_result(6.0) == "6"
    assert calculator.format_result(2.5) == "2.5"
    assert calculator.format_result(1234.0) == "1\u00a0234"


def test_percent_helpers():
    assert calculator.percent_of(200, 10) == 20
    assert calculator.percent_change(100, 150) == 50
    assert calculator.percent_change(100, 50) == -50
    assert calculator.percent_change(0, 0) == 0


def test_loan_maths():
    payment, total, overpay = calculator.loan_payment(120000, 0, 12)
    assert payment == pytest.approx(10000)
    assert total == pytest.approx(120000)
    assert overpay == pytest.approx(0)

    payment, total, overpay = calculator.loan_payment(1000000, 12, 24)
    assert payment > 1000000 / 24  # interest makes each payment larger
    assert total > 1000000
    assert overpay == pytest.approx(total - 1000000)


def test_loan_rejects_zero_term():
    with pytest.raises(ValidationError):
        calculator.loan_payment(1000, 10, 0)
