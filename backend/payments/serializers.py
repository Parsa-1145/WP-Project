from rest_framework import serializers
from .models import BailRequest, PaymentTransaction

class BailRequestSerializer(serializers.Serializer):
    class Meta:
        model = BailRequest
        fields = "__all__"

    def create(self, validated_data):
        return BailRequest.objects.create(**validated_data)