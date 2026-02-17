from rest_framework import serializers
from .models import Complaint, CrimeScene
from accounts.models import User
from django.core.exceptions import ValidationError
from accounts.serializers.fields import NationalIDField, PhoneNumberField

class ComplaintSerializer(serializers.ModelSerializer):
    complainant_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        write_only=True
    )

    class Meta:
        model = Complaint
        fields = ["id", "title", "description", "complainant_national_ids", "complainants"]
        read_only_fields = ["complainants"]

    def create(self, validated_data):
        national_ids = validated_data.pop("complainant_national_ids")
        creator:User = self.context["request"].user

        complaint = Complaint.objects.create(creator=creator, **validated_data)

        users = list(User.objects.filter(national_id__in=national_ids))
        if creator.national_id not in national_ids:
            users.append(creator)

        complaint.complainants.set(users)

        return complaint

class WitnessItemSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    national_id = NationalIDField(should_exist=True)

class CrimeSceneSerializer(serializers.ModelSerializer):
    witnesses = WitnessItemSerializer(many=True, required=True)

    class Meta:
        model = CrimeScene
        fields = ["id", "title", "description", "witnesses"]
    
    def validate_witnesses(self, witnesses):
        counts = {}
        for w in witnesses:
            nid = w.get("national_id")
            counts[nid] = counts.get(nid, 0) + 1

        indexed_errors = {}
        for i, w in enumerate(witnesses):
            nid = w.get("national_id")
            if counts.get(nid, 0) > 1:
                indexed_errors[str(i)] = {
                    "national_id": [f"Duplicate national_id: {nid}."]
                }

        if indexed_errors:
            raise serializers.ValidationError(indexed_errors)

        return witnesses

    def create(self, validated_data):
        return super().create(validated_data)