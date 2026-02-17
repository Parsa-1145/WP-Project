from rest_framework.serializers import ModelSerializer
from accounts.models import User
import re
from .fields import PhoneNumberField, NationalIDField

class UserSerializer(ModelSerializer):
    phone_number = PhoneNumberField()
    national_id = NationalIDField()

    class Meta:
        model = User
        fields = ["password", "username", "first_name", "last_name", "email", "national_id", "phone_number"]

    def create(self, validated_data:dict[str, any]):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)