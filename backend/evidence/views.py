from rest_framework import viewsets
from .serializers import *
from .permissions import IsRecorderOrDjangoModelPermissions


class EvidenceListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Evidence.objects.all().select_related(
        "witnessevidence",
        "bioevidence",
        "vehicleevidence",
        "identityevidence"
    )
    serializer_class = EvidencePolymorphicSerializer
    permission_classes = [IsRecorderOrDjangoModelPermissions]

    def get_queryset(self):
        
        user = self.request.user
        
        if user.has_perm('evidence.view_evidence'):
            return super().get_queryset()
        
        return super().get_queryset().filter(recorder=user)
    

class WitnessEvidenceViewSet(viewsets.ModelViewSet):
    queryset = WitnessEvidence.objects.all()
    serializer_class = WitnessEvidenceSerializer
    permission_classes = [IsRecorderOrDjangoModelPermissions]


class BioEvidenceViewSet(viewsets.ModelViewSet):
    queryset = BioEvidence.objects.all()
    serializer_class = BioEvidenceSerializer
    permission_classes = [IsRecorderOrDjangoModelPermissions]

class VehicleEvidenceViewSet(viewsets.ModelViewSet):
    queryset = VehicleEvidence.objects.all()
    serializer_class = VehicleEvidenceSerializer
    permission_classes = [IsRecorderOrDjangoModelPermissions]


class IdentityEvidenceViewSet(viewsets.ModelViewSet):
    queryset = IdentityEvidence.objects.all()
    serializer_class = IdentityEvidenceSerializer
    permission_classes = [IsRecorderOrDjangoModelPermissions]