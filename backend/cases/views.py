from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer
from rest_framework import serializers
from evidence.serializers import EvidencePolymorphicSerializer
from .models import Case
from evidence.models import Evidence  

from .models import Case, CaseSubmissionLink, CaseSuspectLink
from .serializers import CaseListSerializer, ComplainantCaseListSerializer, CaseUpdateSerializer, CaseLinkedSubmissionSerializer
from evidence.models import Evidence
from evidence.serializers import EvidencePolymorphicSerializer

from investigation.serializers import DetectiveBoardSerializer
from investigation.permissions import IsDetectiveBoardOwner
from investigation.models import DetectiveBoard
from accounts.models import User

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
                "complainants": [
                    {
                        "id": 1,
                        "first_name": "P",
                        "second_name": "Q",
                        "national_id": "1111111111",
                    }
                ],
                "suspects": [
                    {
                        "id": 2,
                        "first_name": "S",
                        "second_name": "T",
                        "national_id": "2222222222",
                        "suspect_link": 9,
                    }
                ],
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





@extend_schema_view(
    get=extend_schema(
        summary="Retrieve case (full details)",
        description=(
            "Returns full case details for users who are assigned as lead detective/supervisor "
            "or have `cases.view_all_cases`. "
            "Complainants are blocked from this endpoint even if they have `cases.view_all_cases`."
        ),
        responses=CaseListSerializer,
    ),
    patch=extend_schema(
        summary="Update case",
        description=(
            "Partially update a case. "
            "Only the assigned lead detective can update case data."
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
    ),
)
class CaseUpdateView(AssignedCaseAccessMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = (
        Case.objects
        .select_related("lead_detective", "supervisor")
        .prefetch_related("complainants")
    )
    http_method_names = ["get", "patch"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CaseListSerializer
        return CaseUpdateSerializer

    def get_object(self):
        user = self.request.user

        if self.request.method == "PATCH":
            case = self.get_case()
            if case.lead_detective_id != user.id:
                raise PermissionDenied("Only the assigned lead detective can update this case.")
            return case

        case = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        complainant_ids = {complainant.id for complainant in case.complainants.all()}
        if user.id in complainant_ids:
            raise PermissionDenied("Complainants cannot access full case details.")

        if user.has_perm("cases.view_all_cases"):
            return case

        if case.lead_detective_id == user.id or case.supervisor_id == user.id:
            return case

        raise PermissionDenied("Only assigned detective/supervisor or users with view_all_cases can access this case.")


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



@extend_schema_view(
    get=extend_schema(
        summary="Retrieve or update detective board of a case",
        description=(
            "Detective board is a JSON structure that assigned detectives can use to organize their investigation. "
            "Only assigned lead detective or supervisor can access or modify the board."
            "The board_json field is null by default and can be updated with a custom JSON structure. "
        ),
        responses=DetectiveBoardSerializer,
        examples=[
            OpenApiExample(
                name="Detective board response",
                response_only=True,
                status_codes=["200"],
                value={
                    "board_json": {
                        "any json structure": 1,
                        "other content": "string",
                    }
                },
            ),
        ]
    ),
    put=extend_schema(
        summary="Update detective board of a case",
        description=(
            "update the detective board JSON. "
            "Only assigned lead detective or supervisor can modify the board. "
        ),
        request=DetectiveBoardSerializer,
        responses=DetectiveBoardSerializer,
        examples=[
            OpenApiExample(
                name="Detective board update request",
                request_only=True,
                value={
                    "board_json": {
                        "any_new_json": "board content",
                    }
                },
            ),
            OpenApiExample(
                name="Detective board update response",
                response_only=True,
                status_codes=["200"],
                value={
                    "board_json": {
                        "any_new_json": "board content",
                    }
                },
            )
        ]
    )
)
class DetectiveBoardUpdateView(AssignedCaseAccessMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DetectiveBoardSerializer

    http_method_names = ["get", "put"]

    def get_object(self):
        case = self.get_case()
        board, _ = DetectiveBoard.objects.get_or_create(case=case)
        return board


@extend_schema_view(
    get=extend_schema(
        examples=[
            OpenApiExample(
                name="Response example",
                response_only=True,
                status_codes=["200"],
                value={"modules":["COMPLAINANT_CASES"]}
            )
        ],
        responses= inline_serializer(
            name="AllowedStringsResponse",
            fields={
                # spectacular treats this as the top-level schema when used as a response
                "modules": serializers.ListField(
                    child=serializers.ChoiceField(choices=["ASSIGNED_CASES", "COMPLAINANT_CASES", "AUTOPSY"]),
                    allow_empty=True,
                )
            },
        )
    )
)
class FrontModulesGetView(APIView):
    def get(self, request):
        user:User = request.user

        if (user is None) or (not user.is_authenticated):
            return Response({"modules":[]})


        items = []

        if user.has_perm("cases.investigate_on_case") or user.has_perm("cases.supervise_case"):
            items.append("ASSIGNED_CASES")

        if user.has_perm("evidence.can_approve_bioevidence"):
            items.append("AUTOPSY")

        items.append("COMPLAINANT_CASES")

        return Response({"modules":items})
