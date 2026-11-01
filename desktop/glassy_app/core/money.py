"""Exact money handling.

Amounts are stored as signed integers in minor units (kopecks/cents) so that
arithmetic never accumulates binary floating point error. Never use float for
money anywhere in this application.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from .errors import ValidationError

# Number of minor units in one major unit. Two decimal places covers every
# currency this app targets.
SCALE = 100

CURRENCY_SYMBOLS = {
    "RUB": "\u20bd",
    "USD": "$",
    "EUR": "\u20ac",
    "GBP": "\u00a3",
    "KZT": "\u20b8",
    "UAH": "\u20b4",
}


def to_minor(value):
    """Convert a user supplied value to integer minor units.

    Accepts int, Decimal, str or float. Strings may use either a comma or a
    dot as the decimal separator, and may contain spaces and a currency
    symbol, because that is what people actually paste into a form.
    """
    if value is None or value == "":
        raise ValidationError("Amount is required", field="amount")

    if isinstance(value, bool):
        raise ValidationError("Amount must be a number", field="amount")

    if isinstance(value, int):
        return value * SCALE

    if isinstance(value, float):
        # Convert through str to avoid the 0.1 + 0.2 class of surprises.
        value = repr(value)

    if isinstance(value, Decimal):
        dec = value
    else:
        text = str(value).strip()
        if not text:
            raise ValidationError("Amount is required", field="amount")
        # Keep digits, separators and a leading sign; drop currency symbols
        # and thousands separators.
        cleaned = []
        for ch in text:
            if ch.isdigit() or ch in ",.-+":
                cleaned.append(ch)
        text = "".join(cleaned)
        # A comma is treated as the decimal separator unless a dot is present.
        if "," in text and "." not in text:
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
        try:
            dec = Decimal(text)
        except InvalidOperation:
            raise ValidationError(f"{value!r} is not a valid amount", field="amount")

    if not dec.is_finite():
        raise ValidationError("Amount must be a finite number", field="amount")

    quantised = (dec * SCALE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(quantised)


def to_decimal(minor):
    """Return the Decimal value of an integer minor-unit amount."""
    if minor is None:
        return Decimal("0")
    return (Decimal(int(minor)) / SCALE).quantize(Decimal("0.01"))


def format_amount(minor, currency="RUB", with_symbol=True, sign=False):
    """Render a minor-unit amount for display.

    Thousands are grouped with a non-breaking space, which is the convention
    for both Russian and most European locales.
    """
    dec = to_decimal(minor)
    negative = dec < 0
    body = f"{abs(dec):,.2f}".replace(",", "\u00a0")
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if with_symbol:
        body = f"{body}\u00a0{symbol}"
    if negative:
        return f"-{body}"
    if sign:
        return f"+{body}"
    return body


def sum_minor(values):
    """Sum an iterable of minor-unit amounts without float error."""
    return sum(int(v or 0) for v in values)


def percent(part, whole):
    """Return ``part / whole`` as a float percentage, guarding zero."""
    whole = int(whole or 0)
    if whole == 0:
        return 0.0
    return (int(part or 0) / whole) * 100.0
