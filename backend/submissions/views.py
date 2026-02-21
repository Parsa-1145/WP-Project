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
        if not st_cls.api_request_schema:
            continue
        variants.append(
            inline_serializer(
                name=f"{st_cls.__name__}CreateRequest",
                fields={
                    "submission_type": serializers.ChoiceField(choices=[(type_key, st_cls.display_name)]),
                    "payload": st_cls.api_request_schema,
                },
            )
        )

    return PolymorphicProxySerializer(
        component_name="SubmissionCreateRequest",
        serializers=variants,
        resource_type_field_name="submission_type",
    )


def _submission_response_example(type_key, st_cls):
    if st_cls.can_be_created_from_request:
        actions_history = [
            {
                "id": 1,
                "submission": 1,
                "action_type": "SUBMIT",
                "payload": {},
                "created_by": 1,
                "created_at": "2026-02-19T00:00:00Z",
            }
        ]
        created_by = 1
    else:
        # System-created submission types usually have no creator and submit action.
        actions_history = []
        created_by = None

    return {
        "id": 1,
        "submission_type": type_key,
        "status": SubmissionStatus.PENDING,
        "target": st_cls.api_response_target_example,
        "actions_history": actions_history,
        "available_actions": [],
        "action_prompt": "",
        "created_by": created_by,
        "created_at": "2026-02-19T00:00:00Z",
    }


def submission_create_examples():
    examples = []
    for type_key, st_cls in SUBMISSION_TYPES.items():
        if st_cls.can_be_created_from_request and st_cls.api_request_payload_example:
            examples.append(
                OpenApiExample(
                    name=f"{st_cls.display_name} request",
                    value={
                        "submission_type": type_key,
                        "payload": st_cls.api_request_payload_example,
                    },
                    request_only=True,
                )
            )

        if st_cls.can_be_created_from_request and st_cls.api_response_target_example:
            examples.append(
                OpenApiExample(
                    name=f"{st_cls.display_name} response",
                    value=_submission_response_example(type_key, st_cls),
                    response_only=True,
                    status_codes=["201"],
                )
            )
    return examples


def submission_get_examples(*, include_system: bool = True):
    examples = []
    for type_key, st_cls in SUBMISSION_TYPES.items():
        if not include_system and not st_cls.can_be_created_from_request:
            continue
        if st_cls.api_response_target_example:
            examples.append(
                OpenApiExample(
                    name=f"{st_cls.display_name} response",
                    value=_submission_response_example(type_key, st_cls),
                    response_only=True,
                    status_codes=["200"],
                )
            )
    return examples


def submission_mine_examples():
    examples = []
    for type_key, st_cls in SUBMISSION_TYPES.items():
        if not st_cls.can_be_created_from_request:
            continue
        if st_cls.api_response_target_example:
            examples.append(
                OpenApiExample(
                    name=f"Mine {st_cls.display_name}",
                    value=_submission_response_example(type_key, st_cls),
                    response_only=True,
                    status_codes=["200"],
                )
            )
    return examples


def submission_inbox_examples():
    examples = []
    for type_key, st_cls in SUBMISSION_TYPES.items():
        if st_cls.api_response_target_example:
            examples.append(
                OpenApiExample(
                    name=f"Inbox {st_cls.display_name}",
                    value=_submission_response_example(type_key, st_cls),
                    response_only=True,
                    status_codes=["200"],
                )
            )
    return examples

@extend_schema(
    request=submission_create_request_schema(),
    responses=SubmissionSerializer,
    examples=submission_create_examples(),
    description="Create a submission with a type.",
    summary="Create submission"
)
class SubmissionCreateView(generics.CreateAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=SubmissionSerializer
    queryset = models.Submission.objects.all()

@extend_schema(
    description=(
        "Retrieve a single submission by ID. "
        "Visible to the creator and users assigned to the submission's current stage "
        "(either by `target_user` or required stage permission)."
    ),
    summary="Get submission",
    responses={
        200: SubmissionSerializer,
        403: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
    examples=submission_get_examples(include_system=True),
)
class SubmissionGetView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionSerializer
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
            .annotate(can_see=Exists(current_stage_match))
            .filter(Q(created_by=user) | Q(can_see=True))
            .distinct()
        )
    
@extend_schema(
        description=(
            "Get the submissions created by the user"
        ),
        summary="Get user submissions",
        responses=SubmissionSerializer(many=True),
        examples=submission_mine_examples(),
    )
class SubmissionMineListView(generics.ListAPIView):
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
        "Returns pending submissions currently assigned to the authenticated user. "
        "A submission appears in the inbox when the user is the target user for the current stage "
        "or has the required permission for that stage."
    ),
    summary="Get submissions in the inbox",
    responses=SubmissionSerializer(many=True),
    examples=submission_inbox_examples(),
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
    summary="Get available submission types to create",
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
            if cls.can_user_submit(request.user):
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
                        name="Accept",
                        fields={
                            "action_type": serializers.ChoiceField(choices=["Accept"]),
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
                OpenApiExample("Accept", value={"action_type": "ACCEPT", "payload":{}}, request_only=True),
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
            "Get action the history of the submission"
        ),
        summary="Get action history",
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
    summary="Get available actions to perform",
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
        return Response({"actions": actions, "prompt": stage.prompt})
