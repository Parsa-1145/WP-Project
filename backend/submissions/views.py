from rest_framework import generics
from django.http import HttpRequest
from .serializers.classes import SubmissionSerializer, SubmissionActionSerializer, Submission, SubmissionAction, SubmissionStatus, SubmissionStage
from rest_framework.permissions import IsAuthenticated
from submissions.submissiontypes.registry import SUBMISSION_TYPES
from drf_spectacular.utils import extend_schema_view ,extend_schema, OpenApiExample, inline_serializer, PolymorphicProxySerializer
from rest_framework import serializers
from . import models
from django.db.models import Exists, OuterRef, F, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from submissions.submissiontypes.registry import get_submission_type
from django.db import transaction

def submission_create_request_schema():
    variants = []

    for type_key, st_cls in SUBMISSION_TYPES.items():
        payload_ser = st_cls.serializer_class

        variants.append(
            inline_serializer(
                name=f"{st_cls.__name__}CreateRequest",
                fields={
                    "submission_type": serializers.ChoiceField(choices=[(type_key, st_cls.display_name)]),
                    "payload": payload_ser(),
                },
            )
        )

    return PolymorphicProxySerializer(
        component_name="SubmissionCreateRequest",
        serializers=variants,
        resource_type_field_name="submission_type",
    )


def submission_create_examples():
    examples = []
    for type_key, st_cls in SUBMISSION_TYPES.items():
        payload_ser = st_cls.serializer_class()

        payload_example = {}
        for name, field in payload_ser.fields.items():
            if field.read_only:
                continue

            if getattr(field, "many", False) or getattr(field, "child", None):
                payload_example[name] = ["string"]
            elif field.__class__.__name__ in ("IntegerField",):
                payload_example[name] = 0
            elif field.__class__.__name__ in ("BooleanField",):
                payload_example[name] = False
            else:
                payload_example[name] = "string"

        examples.append(
            OpenApiExample(
                name=st_cls.display_name,
                value={
                    "submission_type": type_key,
                    "payload": payload_example,
                },
                request_only=True,
            )
        )
    return examples
@extend_schema_view(
    post=extend_schema(
        request=submission_create_request_schema(),
        responses=SubmissionSerializer,
        examples=submission_create_examples()
    )
)
class SubmissionListCreateView(generics.ListCreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=SubmissionSerializer
    queryset = models.Submission.objects.all()

    def get_queryset(self):
        user = self.request.user
        user_perms = list(user.get_all_permissions())

        return (
            models.Submission.objects.filter(
                created_by=user
            )
            .distinct()
        )
    
class SubmissionInboxListView(generics.ListAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=SubmissionSerializer
    queryset = models.Submission.objects.all()

    def get_queryset(self):
        user = self.request.user
        user_perms = list(user.get_all_permissions())

        current_stage_match = SubmissionStage.objects.filter(
            submission_id=OuterRef("pk"),
            order=OuterRef("current_stage"),
        ).filter(
            Q(target_user=user) | Q(target_permission__in=user_perms)
        )

        return (
            Submission.objects
            .filter(status=SubmissionStatus.PENDING)
            .annotate(can_see=Exists(current_stage_match))
            .filter(can_see=True)
        )
class SubmissionTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        out = []
        for cls in SUBMISSION_TYPES.values():
            if cls.does_user_have_access(request.user):
                out.append({"key": cls.type_key, "name": cls.display_name})
        return Response(out)

class SubmissionActionCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionActionSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["submission"] = get_object_or_404(Submission, pk=self.kwargs["pk"])
        return ctx

    @transaction.atomic
    def perform_create(self, serializer):
        submission:Submission = self.get_serializer_context()["submission"]
        action: SubmissionAction = serializer.save(submission=submission, created_by=self.request.user)

        get_submission_type(submission.submission_type).handle_submission_action(submission, action, context={"request": self.request})