from rest_framework import serializers
from .models import Complaint, CrimeScene
from accounts.models import User
from django.core.exceptions import ValidationError
from accounts.serializers.fields import NationalIDField, PhoneNumberField

class ComplaintSerializer(serializers.ModelSerializer):
    complainant_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        write_only=True,
        required=False,   # allow partial updates without sending this field
    )

    class Meta:
        model = Complaint
        fields = ["id", "title", "description", "complainant_national_ids", "complainants"]
        read_only_fields = ["complainants"]

    def validate_complainant_national_ids(self, national_ids):
        # optional: dedupe while preserving order
        seen = set()
        deduped = []
        for nid in national_ids:
            if nid not in seen:
                seen.add(nid)
                deduped.append(nid)
        return deduped
    

    def create(self, validated_data):
        national_ids = validated_data.pop("complainant_national_ids")
        creator = self.context["request"].user

        complaint = Complaint.objects.create(creator=creator, **validated_data)

        users = list(User.objects.filter(national_id__in=national_ids))
        if creator.national_id not in national_ids:
            users.append(creator)

        complaint.complainants.set(users)
        return complaint

    def update(self, instance, validated_data):
        creator = self.context["request"].user

        # update scalar fields
        for field in ("title", "description"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        # update complainants if provided
        if "complainant_national_ids" in validated_data:
            national_ids = validated_data.pop("complainant_national_ids")

            users = list(User.objects.filter(national_id__in=national_ids))
            # ensure updater is included (same rule as create)
            if creator.national_id not in national_ids:
                users.append(creator)

            instance.complainants.set(users)

        instance.save()
        return instance

class WitnessItemSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    national_id = NationalIDField(should_exist=True)

class CrimeSceneSerializer(serializers.ModelSerializer):
    witnesses = WitnessItemSerializer(many=True, required=True)

    class Meta:
        model = CrimeScene
        fields = ["id", "title", "description", "witnesses", "crime_datetime"]
    
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
    



