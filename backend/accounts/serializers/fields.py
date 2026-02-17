from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from accounts import validators
from accounts.models import User
import re

def normalize_phone_number(value: str) -> str:
    raw = str(value or "").strip()

    if raw.startswith("+"):
        s = "+" + re.sub(r"\D", "", raw[1:])
    else:
        s = re.sub(r"\D", "", raw)

    if s.startswith("0098"):
        s = "+98" + s[4:]
    elif s.startswith("98"):
        s = "+98" + s[2:]
    elif s.startswith("09"):
        s = "+98" + s[1:]

    return s

class NationalIDField(serializers.CharField):
    default_error_messages = {
        "invalid": "National ID must be exactly 10 digits.",
        "required": "National Id is required.",
        "not_found": "National Id {value} doesn't exist.",
    }

    def __init__(self, *args, should_exist: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_exist = should_exist

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value = str(value).strip()

        if not value:
            raise DRFValidationError(self.error_messages["required"])

        try:
            validators.validate_national_id(value)
        except DjangoValidationError:
            raise DRFValidationError(self.error_messages["invalid"])
        
        if self.should_exist:
            if not User.objects.filter(national_id=value).exists():
                raise DRFValidationError(self.error_messages["not_found"].format(value=value))


        return value
    
class PhoneNumberField(serializers.CharField):
    default_error_messages = {
        "invalid": "Invalid Iranian mobile number. Use +989XXXXXXXXX.",
        "required": "Phone number is required.",
    }

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        normalized = normalize_phone_number(value)

        if not normalized:
            raise DRFValidationError(self.error_messages["required"])

        try:
            validators.validate_phone_number(normalized)
        except DjangoValidationError:
            raise DRFValidationError(self.error_messages["invalid"])

        return normalized
