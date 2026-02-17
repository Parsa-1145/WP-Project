from rest_framework import serializers
from .models import *

class WitnessEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WitnessEvidence
        fields = "__all__"


class BioEvidenceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BioEvidenceImage
        fields = ['id', 'image', 'uploaded_at']

class BioEvidenceSerializer(serializers.ModelSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    images = BioEvidenceImageSerializer(many=True, read_only=True)

    class Meta:
        model = BioEvidence
        fields = "__all__"

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        bio_evidence = BioEvidence.objects.create(**validated_data)

        for image in uploaded_images:
            BioEvidenceImage.objects.create(evidence=bio_evidence, image=image)

        return bio_evidence

class VehicleEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEvidence
        fields = "__all__"
    
    def validate(self, data):
        plate = data.get('plate_number')
        serial = data.get('serial_number')

        if plate and serial:
            raise serializers.ValidationError("A vehicle cannot have both a license plate and a serial number.")
        if not plate and not serial:
            raise serializers.ValidationError("Vehicle must have at least a license plate or a serial number.")
        return data
    
class IdentityEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityEvidence
        fields = "__all__"


class EvidencePolymorphicSerializer(serializers.Serializer):
    resource_type = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = "__all__"
    
    def get_resource_type(self, obj):
        return obj.__class__.__name__

    def to_representation(self, instance):
        if isinstance(instance, WitnessEvidence):
            return WitnessEvidenceSerializer(instance).data
        elif isinstance(instance, BioEvidence):
            return BioEvidenceSerializer(instance).data
        elif isinstance(instance, VehicleEvidence):
            return VehicleEvidenceSerializer(instance).data
        elif isinstance(instance, IdentityEvidence):
            return IdentityEvidenceSerializer(instance).data
        else:
            return super().to_representation(instance)
