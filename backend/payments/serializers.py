from rest_framework import serializers
from .models import BailRequest, PaymentTransaction, DataForReward

class BailRequestSerializer(serializers.Serializer):
    class Meta:
        model = BailRequest
        fields = "__all__"

    def create(self, validated_data):
        return BailRequest.objects.create(**validated_data)
    
class DataForRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataForReward
        fields = ["id", "reward", "description"]
        read_only_fields = ["id", "reward"]

    def create(self, validated_data):
        return DataForReward.objects.create(**validated_data)