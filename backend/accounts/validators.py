from django.core import validators
from django.core.exceptions import ValidationError
import re

IR_NID_10_DIGITS = re.compile(r"^\d{10}$")

def validate_national_id(value: str) -> None:
    """
    Validates national id. Only accepts strings which exactly contain 10 digits.
    """
    if value is None or not IR_NID_10_DIGITS.fullmatch(str(value).strip()):
        raise ValidationError("National ID must be exactly 10 digits.")


E164_IRAN_MOBILE_RE = re.compile(r"^\+989\d{9}$")

def validate_phone_number(value: str) -> None:
    """
    Validates Iranian mobile numbers in E.164 form: +989XXXXXXXXX
    Accepts input with spaces/dashes/parentheses but validates normalized form.
    """
    if value is None:
        raise ValidationError("Phone number is required.")

    raw = str(value).strip()

    if raw.startswith("+"):
        normalized = "+" + re.sub(r"\D", "", raw[1:])
    else:
        normalized = re.sub(r"\D", "", raw)

    if normalized.startswith("0098"):
        normalized = "+98" + normalized[4:]
    elif normalized.startswith("98"):
        normalized = "+98" + normalized[2:]
    elif normalized.startswith("09"):
        normalized = "+98" + normalized[1:]

    if not E164_IRAN_MOBILE_RE.fullmatch(normalized):
        raise ValidationError("Invalid Iranian mobile number. Use +989XXXXXXXXX.")