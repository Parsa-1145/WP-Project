from rest_framework.serializers import ModelSerializer
from .models import User
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

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["password", "username", "first_name", "last_name", "email", "national_id", "phone_number"]
    
    def validate_national_id(self, value):
        User._meta.get_field("national_id").run_validators(value)
        return value.strip()
    
    def validate_phone_number(self, value):
        value = normalize_phone_number(value)
        User._meta.get_field("phone_number").run_validators(value)
        return value

    def create(self, validated_data:dict[str, any]):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)