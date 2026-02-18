from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, PolymorphicProxySerializer, OpenApiExample
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .serializers import *
from .permissions import IsRecorderOrDjangoModelPermissions


serializers_map = {
    'witness': WitnessEvidenceSerializer,
    'bio': BioEvidenceSerializer,
    'vehicle': VehicleEvidenceSerializer,
    'identity': IdentityEvidenceSerializer,
    'other': OtherEvidenceSerializer
}

evidence_response_schema = PolymorphicProxySerializer(
    component_name='EvidenceResponse',
    serializers={
        'WitnessEvidence': WitnessEvidenceSerializer,
        'BioEvidence': BioEvidenceSerializer,
        'VehicleEvidence': VehicleEvidenceSerializer,
        'IdentityEvidence': IdentityEvidenceSerializer,
    },
    resource_type_field_name='resource_type',
)

request_examples = [
    OpenApiExample(
        "Witness Example",
        summary="Witness Evidence Example",
        value={
            'type': 'witness',
            'title': 'string',
            'description': 'string',
            'case': 1,
            'media_file': 'file',
            'transcript': 'string'
        },
        media_type='multipart/form-data',
        request_only=True
    ),
    OpenApiExample(
        "Vehicle Example",
        summary="Vehicle Evidence Example",
        value={
            'type': 'vehicle',
            'title': 'string',
            'description': 'string',
            'case': 1,
            'model_name': 'string',
            'color': 'string',
            'plate_number': 'one of plate or serial must be provided',
            'serial_number': 'one of plate or serial must be provided'
        },
        media_type='multipart/form-data',
        request_only=True
    ),
    OpenApiExample(
        "Identity Example",
        summary="Identity Evidence Example",
        description="Identity evidence can include details about a person relevant to the case. The 'details' field can be a JSON string containing key-value pairs of information such as date of birth, address, or any other pertinent details.",
        value={
            'type': 'identity',
            'title': 'string',
            'description': 'string',
            'case': 1,
            'full_name': 'string',
            'details': "{'key': 'value','another_key': 'another_value'}"
        },
        media_type='multipart/form-data',
        request_only=True
    ),
    OpenApiExample(
        "Bio Example",
        summary="Biological Evidence Example",
        value={
            'type': 'bio',
            'title': 'string',
            'description': 'string',
            'case': 1,
            'uploaded_images': [
                '(Binary Image File 1)',
                '(Binary Image File 2)'
            ]
        },
        media_type='multipart/form-data',
        request_only=True
    ),
    OpenApiExample(
        "Other Example",
        summary="Other Evidence Example",
        value={
            'type': 'other',
            'title': 'string',
            'description': 'string',
            'case': 1,
        },
        media_type='multipart/form-data',
        request_only=True
    )
]

response_examples = [
    OpenApiExample(
        "Witness Response",
        summary="Witness Evidence Response",
        value={
            "id": 1,
            "media_file": "http://127.0.0.1:8000/media/evidence/witness/image.png",
            "title": "string",
            "description": "string",
            "created_at": "2026-02-18T14:01:51.213174+03:30",
            "transcript": "string",
            "case": 1,
            "recorder": 1,
            "resource_type": "WitnessEvidence"
        },
        response_only=True,
        status_codes=[200, 201]
    ),
    OpenApiExample(
        "Vehicle Response",
        summary="Vehicle Evidence Response",
        value={
        "id": 3,
        "title": "string",
        "description": "string",
        "created_at": "2026-02-18T14:39:44.795085+03:30",
        "model_name": "string",
        "color": "string",
        "plate_number": "string",
        "serial_number": None,
        "case": 1,
        "recorder": 1,
        "resource_type": "VehicleEvidence"
        },
        response_only=True,
        status_codes=[200, 201]
    ),
    OpenApiExample(
        "Identity Response",
        value={
        "id": 4,
        "title": "string",
        "description": "string",
        "created_at": "2026-02-18T14:40:35.345465+03:30",
        "full_name": "string",
        "details": {
            "key": "value",
            "key2": "value2"
        },
        "case": 1,
        "recorder": 1,
        "resource_type": "IdentityEvidence"
        },
    ),
     OpenApiExample(
        "Bio Response",
        summary="Bio Evidence Response",
        value={
        "id": 5,
        "title": "string",
        "description": "string",
        "created_at": "2026-02-18T14:41:15.297780+03:30",
        "coroner_result": "string",
        "images": [
            {
                "id": 1,
                "image": "http://127.0.0.1:8000/media/evidence/bio/image.jpg",
                "uploaded_at": "2026-02-18T14:41:29.854313+03:30"
            }
        ],
        "is_verified": True,
        "case": 1,
        "recorder": 1,
        "resource_type": "BioEvidence"
        },
        response_only=True,
        status_codes=[200, 201]
    ),
]

@extend_schema_view(
    list=extend_schema(
        summary="List all evidence",
        responses={200: evidence_response_schema},
        examples=response_examples
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific evidence by ID",
        responses={200: evidence_response_schema},
        examples=response_examples
    ),
)
class EvidenceViewSet(viewsets.ModelViewSet):    

    queryset = Evidence.objects.all().select_related(
        "witnessevidence",
        "bioevidence",
        "vehicleevidence",
        "identityevidence",
        "otherevidence"
    )
    serializer_class = EvidencePolymorphicSerializer
    permission_classes = [IsRecorderOrDjangoModelPermissions]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        
        if user.has_perm('evidence.view_evidence'):
            return super().get_queryset()
        
        return super().get_queryset().filter(recorder=user)
    

    @extend_schema(
        request={
            'multipart/form-data': PolymorphicProxySerializer(
            component_name="EvidenceCreateRequest",
            serializers=serializers_map,
            resource_type_field_name="type"
        )
        },
        examples=request_examples + response_examples,
        responses={201: evidence_response_schema},
        description="Create new evidence. The request must include a 'type' field indicating the evidence type (witness, bio, vehicle, identity, other)."
    )
    def create(self, request, *args, **kwargs):

        evidence_type = request.data.get('type')

    

        serializer_class = serializers_map.get(evidence_type)


        if not serializer_class:
            return Response(
                {"error": "Invalid evidence type. Must be one of: witness, bio, vehicle, identity."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(recorder=request.user)


        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @extend_schema(
        request={
            'multipart/form-data': PolymorphicProxySerializer(
                component_name="EvidenceUpdateRequest",
                serializers=serializers_map,
                resource_type_field_name="type"
            )
        },
        examples=request_examples + response_examples,
        responses={200: evidence_response_schema},
        description="Update existing evidence. Only the recorder of the evidence can update it."
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        evidence_type = instance.get_evidence_type_display().lower()


        serializer_class = serializers_map.get(evidence_type)

        if not serializer_class:
            return Response(
                {"error": "Invalid evidence type. Cannot update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = serializer_class(instance, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
