from rest_framework import generics
from django.http import HttpRequest
from .serializers.classes import SubmissionSerializer, SubmissionActionSerializer, Submission, SubmissionAction, SubmissionStatus, SubmissionStage
from rest_framework.permissions import IsAuthenticated
from submissions.submissiontypes.registry import SUBMISSION_TYPES
from drf_spectacular.utils import extend_schema_view ,extend_schema, OpenApiExample, inline_serializer, PolymorphicProxySerializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from . import models
from django.db.models import Exists, OuterRef, F, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
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
                    "payload": st_cls.api_schema,
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
        examples.append(
            OpenApiExample(
                name=st_cls.display_name,
                value={
                    "submission_type": type_key,
                    "payload": st_cls.api_payload_example,
                },
                request_only=True,
            )
        )
    return examples

@extend_schema_view(
    post=extend_schema(
        request=submission_create_request_schema(),
        responses=SubmissionSerializer,
        examples=submission_create_examples(),
        description="Create a submission with a type.",
        summary="Create submission"
    ),
    get=extend_schema(
        description=(
            "Get the submissions of the user"
        ),
        summary="Get submissions",
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

@extend_schema(
    description=(
        "Get the submission which the current user should do an action on. For example, after a complaint was filled, all cadets will have that complaint in their inbox"
    ),
    summary="Get submissions in the inbox",
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
    
@extend_schema(
    description="Gets the submission types available to the authenticated user.",
    summary="Get available submission types",
    responses={
        200: inline_serializer(
            name="SubmissionAllowedTypes",
            fields={
                "types": serializers.ListField(
                    child=inline_serializer(
                        name="SubmissionTypeItem",
                        fields={
                            "key": serializers.CharField(help_text="Stable identifier used in API requests (submission_type)."),
                            "name": serializers.CharField(help_text="Human-readable display name."),
                        },
                    ),
                    help_text="List of submission types the user is allowed to create/use.",
                )
            },
        ),
        403: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            name="Example response",
            description="User has access to multiple submission types.",
            value={
                "types": [
                    {"key": "CRIME_SCENE", "name": "Crime Scene"},
                    {"key": "COMPLAINT", "name": "Complaint"}
                ]
            },
            response_only=True,
            status_codes=["200"],
        )
    ],
)
class SubmissionTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        out = []
        for cls in SUBMISSION_TYPES.values():
            if cls.does_user_have_access(request.user):
                out.append({"key": cls.type_key, "name": cls.display_name})
        return Response({"types":out})


@extend_schema_view(
    post=extend_schema(
        description=(
            "Performs an action on the submission. For example a cadet rejecting / accepting a submission, Or a user resubmiting the details after rejection\n\n"
            "The request must include `action_type` and, depending on the action, a `payload` "
            "matching the required schema for that action type.\n\n"
            "The action is permitted only if the caller is the current stage target user "
            "or has the required stage permission (i.e., belongs to the target group). "
            "Otherwise, the endpoint returns 403 Forbidden.\n\n"
            "Each action will change the current stage of the submission."
        ),
        summary="Perform an action on submission",
        request= PolymorphicProxySerializer(
                component_name="SubmissionActionCreate",
                resource_type_field_name="action_type",
                serializers=[
                    inline_serializer(
                        name="Resubmit",
                        fields={
                            "action_type": serializers.ChoiceField(choices=["RESUBMIT"]),
                            "payload" : serializers.DictField(
                                required=True
                            )
                        }
                    ),
                    inline_serializer(
                        name="Approve",
                        fields={
                            "action_type": serializers.ChoiceField(choices=["APPROVE"]),
                            "payload": serializers.DictField(required=False, default=dict),
                        },
                    ),
                    inline_serializer(
                        name="Reject",
                        fields={
                            "action_type": serializers.ChoiceField(choices=["REJECT"]),
                            "payload" : inline_serializer(
                                name="payload",
                                fields={
                                    "message" : serializers.CharField()
                                    }
                            )
                        },
                    ),
                ],
            ),
        examples=[
                OpenApiExample("Resubmit", value={
                    "action_type": "RESUBMIT",
                    "payload": {"param1":"data1"}}, request_only=True, description="Payload must match the submission-create payload schema for this submission's submission_type."),
                OpenApiExample("Approve", value={"action_type": "APPROVE", "payload":{}}, request_only=True),
                OpenApiExample("Reject", value={"action_type": "REJECT", "payload":{"message":"Rejection message"}}, request_only=True),
            ],
        responses={
            200: SubmissionActionSerializer,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
    get=extend_schema(
        description=(
            "Get an specific submission action"
        ),
        summary="Get submission action",
    )
)
class SubmissionActionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionActionSerializer

    def get_submission(self) -> Submission:
        if not hasattr(self, "_submission"):
            self._submission = get_object_or_404(Submission, pk=self.kwargs["pk"])
        return self._submission

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["submission"] = self.get_submission()
        return ctx

    def get_queryset(self):
        submission = self.get_submission()

        # TODO check permissions

        return SubmissionAction.objects.filter(submission=submission)

    @transaction.atomic
    def perform_create(self, serializer):
        submission = self.get_submission()

        action = serializer.save(submission=submission, created_by=self.request.user)

        get_submission_type(submission.submission_type).handle_submission_action(
            submission,
            action,
            context={"request": self.request},
        )


@extend_schema(
    description="Gets the actions available to this submission. Returns 403 if not authorized.",
    summary="Get available actions",
    responses={
        200: inline_serializer(
            name="SubmissionAllowedActions",
            fields={
                "actions": serializers.ListField(child=serializers.CharField())
            },
        ),
        403: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
)
class SubmissionActionTypeGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        submission = get_object_or_404(Submission, pk=pk)

        stage = (
            SubmissionStage.objects
            .filter(submission=submission, order=submission.current_stage)
            .first()
        )
        if stage is None:
            raise NotFound("Submission stage corrupted")

        is_target_user = (stage.target_user_id == request.user.id)
        has_target_perm = (
            bool(stage.target_permission) and request.user.has_perm(stage.target_permission)
        )

        if not is_target_user and not has_target_perm:
            raise PermissionDenied()

        if submission.status != SubmissionStatus.PENDING:
            return Response([])

        actions = list(stage.allowed_actions) if stage.allowed_actions is not None else []
        return Response({"actions": actions})