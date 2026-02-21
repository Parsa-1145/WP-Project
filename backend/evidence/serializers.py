from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from .models import *
from cases.models import Case




class BaseEvidenceSerializer(serializers.ModelSerializer):
    def validate_case(self, value):
        request = self.context.get('request')

        if request and not request.user and not request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        
        user = request.user

        if user.has_perm('cases.view_case', value):
            return value
        
        if Case.objects.filter(id=value.id, complainants__in=[user]).exists():
            return value
        raise PermissionDenied("You do not have permission to this case.")


class WitnessEvidenceSerializer(BaseEvidenceSerializer):
    media_file = serializers.FileField(required=False)
    class Meta:
        model = WitnessEvidence
        fields = "__all__"
        read_only_fields = ['recorder']



class BioEvidenceImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()
    class Meta:
        model = BioEvidenceImage
        fields = ['id', 'image', 'uploaded_at']
        

class BioEvidenceSerializer(BaseEvidenceSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    images = BioEvidenceImageSerializer(many=True, read_only=True)

    class Meta:
        model = BioEvidence
        fields = "__all__"
        read_only_fields = ['recorder', 'coroner_result', 'is_verified']

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        bio_evidence = super().create(validated_data)

        for image in uploaded_images:
            BioEvidenceImage.objects.create(evidence=bio_evidence, image=image)

        return bio_evidence

class VehicleEvidenceSerializer(BaseEvidenceSerializer):
    class Meta:
        model = VehicleEvidence
        fields = "__all__"
        read_only_fields = ['recorder']
    
    def validate(self, data):
        plate = data.get('plate_number', getattr(self.instance, 'plate_number', None))
        serial = data.get('serial_number', getattr(self.instance, 'serial_number', None))

        if plate and serial:
            raise serializers.ValidationError("A vehicle cannot have both a license plate and a serial number.")
        if not plate and not serial:
            raise serializers.ValidationError("Vehicle must have at least a license plate or a serial number.")
        return data
    


class IdentityEvidenceSerializer(BaseEvidenceSerializer):
    class Meta:
        model = IdentityEvidence
        fields = "__all__"
        read_only_fields = ['recorder']

class OtherEvidenceSerializer(BaseEvidenceSerializer):
    class Meta:
        model = OtherEvidence
        fields = "__all__"
        read_only_fields = ['recorder']


class EvidencePolymorphicSerializer(serializers.Serializer):
    resource_type = serializers.SerializerMethodField()

    def get_resource_type(self, obj):
        return obj.__class__.__name__

    def to_representation(self, instance):
        if hasattr(instance, 'witnessevidence'):
            data = WitnessEvidenceSerializer(instance.witnessevidence, context=self.context).data
            data['resource_type'] = 'WitnessEvidence'
            return data
            
        elif hasattr(instance, 'bioevidence'):
            data = BioEvidenceSerializer(instance.bioevidence, context=self.context).data
            data['resource_type'] = 'BioEvidence'
            return data
            
        elif hasattr(instance, 'vehicleevidence'):
            data = VehicleEvidenceSerializer(instance.vehicleevidence, context=self.context).data
            data['resource_type'] = 'VehicleEvidence'
            return data
            
        elif hasattr(instance, 'identityevidence'):
            data = IdentityEvidenceSerializer(instance.identityevidence, context=self.context).data
            data['resource_type'] = 'IdentityEvidence'
            return data

        elif hasattr(instance, 'otherevidence'):
            data = OtherEvidenceSerializer(instance.otherevidence, context=self.context).data
            data['resource_type'] = 'OtherEvidence'
            return data

        return super().to_representation(instance)
