from django.shortcuts import render
from rest_framework import generics
from . import serializers as custom_serializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class ComplaintCreateView(generics.CreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=custom_serializer.ComplaintSerializer

class CrimeSceneCreateView(generics.CreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=custom_serializer.CrimeSceneSerializer