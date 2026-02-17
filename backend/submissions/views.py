from django.shortcuts import render
from rest_framework import generics
from django.http import HttpRequest
from .serializers.classes import SubmissionSerializer
from rest_framework.permissions import IsAuthenticated
from submissiontypes.registry import SUBMISSION_TYPES

class SubmissionCreateView(generics.CreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=SubmissionSerializer

class SubmissionsGetView(generics.RetrieveAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=SubmissionSerializer

    def get_queryset(self):

        return super().get_queryset()
    
class SubmissionTypeRetrieveView(generics.RetrieveAPIView):
    def get(self, request: HttpRequest, *args, **kwargs):
        out = []
        for cls in SUBMISSION_TYPES.values():
            if cls.does_user_have_access(request.user):
                out.append({"key": cls.type_key, "name": cls.display_name})
