from django.shortcuts import render
from rest_framework import generics
from . import serializers as custom_serializer
from rest_framework.permissions import IsAuthenticated
from evidence.serializers import EvidencePolymorphicSerializer
from .models import Case
from evidence.models import Evidence  
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

# Create your views here.
class ComplaintCreateView(generics.CreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=custom_serializer.ComplaintSerializer

class CrimeSceneCreateView(generics.CreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=custom_serializer.CrimeSceneSerializer


class CaseEvidenceView(generics.ListAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=EvidencePolymorphicSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')

        case = get_object_or_404(Case, id=pk)
    
        user = self.request.user
        

        if not user.has_perm('cases.view_case') and not case.complainants.filter(id=user.id).exists():
            raise PermissionDenied("You do not have permission to view this case's evidence.")
        
        return Evidence.objects.filter(case_id=pk).select_related(
            "witnessevidence",
            "bioevidence",
            "vehicleevidence",
            "identityevidence",
            "otherevidence"
        )

