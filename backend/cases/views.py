from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import serializers

from .models import Case, CaseSubmissionLink
from .serializers import CaseListSerializer, ComplainantCaseListSerializer, CaseUpdateSerializer, CaseLinkedSubmissionSerializer
from evidence.models import Evidence
from evidence.serializers import EvidencePolymorphicSerializer


@extend_schema(
    summary="List cases (full details)",
    description=(
        "Returns full case details for users who are assigned as lead detective/supervisor "
        "or have `cases.view_all_cases`. "
        "Cases where the caller is a complainant are excluded from this endpoint."
    ),
    responses=CaseListSerializer(many=True),
    examples=[
        OpenApiExample(
            name="Full case list response",
            response_only=True,
            status_codes=["200"],
            value={
                "id": 12,
                "title": "Bank Robbery",
                "description": "Armed robbery at city branch.",
                "crime_datetime": "2026-02-19T10:30:00Z",
                "crime_level": "CR",
                "status": "open",
                "witnesses": [
                    {"phone_number": "+989121234567", "national_id": "1234567890"},
                ],
                "lead_detective": "Alex Carter",
                "supervisor": "Sam Lee",
                "complainant_national_ids": ["1111111111", "2222222222"],
                "suspects_national_ids": ["1111111111", "2222222222"],
            },
        ),
    ],
)
class CaseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Case.objects
            .select_related("lead_detective", "supervisor")
            .prefetch_related("complainants")
        )

        # Complainants never receive the full-detail payload from this endpoint.
        if user.has_perm("cases.view_all_cases"):
            return queryset.exclude(complainants=user).distinct().order_by("-id")

        return (
            queryset
            .filter(Q(lead_detective=user) | Q(supervisor=user))
            .exclude(complainants=user)
            .distinct()
            .order_by("-id")
        )


@extend_schema(
    summary="List complainant cases (limited details)",
    description=(
        "Returns only cases where the caller is a complainant. "
        "Payload is intentionally reduced and never includes sensitive case details."
    ),
    responses=ComplainantCaseListSerializer(many=True),
    examples=[
        OpenApiExample(
            name="Complainant case list response",
            response_only=True,
            status_codes=["200"],
            value={
                "id": 21,
                "title": "Street Assault",
                "crime_datetime": "2026-02-18T19:15:00Z",
                "status": "awaiting_investigator",
                "complainant_national_ids": ["1111111111", "2222222222"]
            },
        ),
    ],
)
class ComplainantCaseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ComplainantCaseListSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Case.objects
            .filter(complainants=user)
            .distinct()
            .order_by("-id")
        )


class AssignedCaseAccessMixin:
    def get_case(self):
        if hasattr(self, "_case_obj"):
            return self._case_obj

        case = get_object_or_404(
            Case.objects.select_related("lead_detective", "supervisor"),
            pk=self.kwargs["pk"],
        )
        user = self.request.user
        if case.lead_detective_id != user.id and case.supervisor_id != user.id:
            raise PermissionDenied("Only assigned detective or supervisor can access this case.")
        self._case_obj = case
        return case





@extend_schema(
    summary="Update case",
    description=(
        "Partially update a case. "
        "Only the assigned lead detective or supervisor can update case data."
    ),
    request=CaseUpdateSerializer,
    responses=CaseUpdateSerializer,
    examples=[
        OpenApiExample(
            name="Patch case",
            request_only=True,
            value={
                "title": "Updated Case Title",
                "description": "Updated summary",
                "complainant_national_ids": ["1111111111", "2222222222"],
                "suspects_national_ids": ["1111111111", "2222222222"],
                "witnesses": [
                    {"phone_number": "+989121234567", "national_id": "3333333333"},
                ],
            },
        ),
    ],
)
class CaseUpdateView(AssignedCaseAccessMixin, generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseUpdateSerializer
    queryset = (
        Case.objects
        .select_related("lead_detective", "supervisor")
        .prefetch_related("complainants")
    )
    http_method_names = ["patch"]

    def get_object(self):
        return self.get_case()


@extend_schema(
    summary="List evidences of a case",
    description="Returns evidences linked to the case. Only assigned lead detective or supervisor can access.",
    responses=EvidencePolymorphicSerializer(many=True),
    examples=[
        OpenApiExample(
            name="Case evidences response",
            response_only=True,
            status_codes=["200"],
            value={
                "id": 7,
                "title": "Broken Glass Sample",
                "description": "Collected from entry point",
                "created_at": "2026-02-20T09:00:00Z",
                "case": 12,
                "recorder": 3,
                "resource_type": "OtherEvidence",
            },
        )
    ],
)
class CaseEvidenceListView(AssignedCaseAccessMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvidencePolymorphicSerializer

    def get_queryset(self):
        case = self.get_case()
        return (
            Evidence.objects
            .filter(case_id=case.id)
            .select_related(
                "witnessevidence",
                "bioevidence",
                "vehicleevidence",
                "identityevidence",
                "otherevidence",
            )
            .order_by("-created_at")
        )


@extend_schema(
    summary="List linked submissions of a case",
    description="Returns submissions linked to the case. Only assigned lead detective or supervisor can access.",
    responses=CaseLinkedSubmissionSerializer(many=True),
    examples=[
        OpenApiExample(
            name="Case submissions response",
            response_only=True,
            status_codes=["200"],
            value={
                "relation": "ORIGIN",
                "submission": {
                    "id": 15,
                    "submission_type": "COMPLAINT",
                    "status": "PENDING",
                    "target": None,
                    "actions_history": [],
                    "available_actions": [],
                    "action_prompt": "",
                    "created_by": 3,
                    "created_at": "2026-02-20T09:10:00Z",
                },
            },
        )
    ],
)
class CaseSubmissionListView(AssignedCaseAccessMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseLinkedSubmissionSerializer

    def get_queryset(self):
        case = self.get_case()
        return (
            CaseSubmissionLink.objects
            .filter(case_id=case.id)
            .select_related("submission", "submission__created_by")
            .prefetch_related("submission__actions_history", "submission__stages")
            .order_by("-submission__created_at")
            .distinct()
        )
