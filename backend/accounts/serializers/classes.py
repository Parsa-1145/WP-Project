from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from accounts.models import User
import re
from .fields import PhoneNumberField, NationalIDField
from payments.models import BailRequest

class UserSerializer(ModelSerializer):
    phone_number = PhoneNumberField()
    national_id = NationalIDField()

    class Meta:
        model = User
        fields = ["password", "username", "first_name", "last_name", "email", "national_id", "phone_number"]

    def create(self, validated_data:dict[str, any]):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)
    
class UserUpdateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["status"]


class CurrentUserSerializer(ModelSerializer):
    has_bail_request = serializers.SerializerMethodField()
    bail_request_id = serializers.SerializerMethodField()
    bail_request_status = serializers.SerializerMethodField()

    def _get_relevant_bail_request(self, obj: User):
        cache = getattr(self, "_bail_request_cache", None)
        if cache is None:
            cache = {}
            self._bail_request_cache = cache

        if obj.pk in cache:
            return cache[obj.pk]

        selected = BailRequest.objects.filter(requested_by=obj).exclude(status=BailRequest.Status.PAID).first()
        cache[obj.pk] = selected
        return selected

    def get_has_bail_request(self, obj: User) -> bool:
        return self._get_relevant_bail_request(obj) is not None

    def get_bail_request_id(self, obj: User):
        bail = self._get_relevant_bail_request(obj)
        return bail.id if bail else None

    def get_bail_request_status(self, obj: User):
        bail = self._get_relevant_bail_request(obj)
        return bail.status if bail else None

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "national_id", "phone_number", "status",
            "has_bail_request", "bail_request_id", "bail_request_status",
        ]
        read_only_fields = fields
