"""Money handling must be exact. These tests pin the tricky cases."""

import pytest

from glassy_app.core import money
from glassy_app.core.errors import ValidationError


def test_parses_common_inputs():
    assert money.to_minor("1234.56") == 123456
    assert money.to_minor("1234,56") == 123456
    assert money.to_minor("1 234,56") == 123456
    assert money.to_minor("1234") == 123400
    assert money.to_minor(1234) == 123400
    assert money.to_minor("0") == 0
    assert money.to_minor("-50.25") == -5025


def test_rounds_half_up():
    assert money.to_minor("0.005") == 1
    assert money.to_minor("0.004") == 0
    assert money.to_minor("1234.565") == 123457


def test_float_input_does_not_leak_binary_error():
    # The classic 0.1 + 0.2 problem must not appear once values are integers.
    assert money.to_minor(0.1) + money.to_minor(0.2) == money.to_minor("0.3")


def test_thousands_of_additions_stay_exact():
    total = sum(money.to_minor("0.01") for _ in range(10000))
    assert total == 10000  # exactly 100.00


@pytest.mark.parametrize("bad", ["", None, "abc", "1.2.3", "  ", True])
def test_rejects_invalid(bad):
    with pytest.raises(ValidationError):
        money.to_minor(bad)


def test_formatting():
    assert money.format_amount(123456, "RUB") == "1\u00a0234.56\u00a0\u20bd"
    assert money.format_amount(-5000, "USD") == "-50.00\u00a0$"
    assert money.format_amount(0, "EUR") == "0.00\u00a0\u20ac"
    assert money.format_amount(100, "RUB", with_symbol=False) == "1.00"
    assert money.format_amount(100, "RUB", sign=True) == "+1.00\u00a0\u20bd"


def test_round_trip():
    for text in ("0.01", "999.99", "1000000.00", "-123.45"):
        assert money.to_decimal(money.to_minor(text)).__str__() == str(
            __import__("decimal").Decimal(text)
        )


def test_percent_guards_zero():
    assert money.percent(5, 0) == 0.0
    assert money.percent(50, 200) == 25.0
