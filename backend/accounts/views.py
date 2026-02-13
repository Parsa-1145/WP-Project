from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework import generics
from rest_framework import permissions
from drf_spectacular.utils import extend_schema, OpenApiExample
from . import serializers as customSerializers 

@extend_schema(
    summary="Sign up",
    description="Create a new user account.",
    request=customSerializers.UserSerializer,
    responses={201: customSerializers.UserSerializer},
)
class SignupView(generics.CreateAPIView):
    serializer_class = customSerializers.UserSerializer
    permission_classes = [permissions.AllowAny]