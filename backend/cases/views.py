from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer
from rest_framework import serializers
from evidence.serializers import EvidencePolymorphicSerializer
from .models import Case
from evidence.models import Evidence  

from .models import Case, CaseSubmissionLink, CaseSuspectLink
from .serializers import (CaseListSerializer, 
                          ComplainantCaseListSerializer,
                            CaseUpdateSerializer,
                              CaseLinkedSubmissionSerializer,
                              MostWantedSerializer)
from evidence.models import Evidence
from evidence.serializers import EvidencePolymorphicSerializer

from investigation.serializers import DetectiveBoardSerializer
from investigation.permissions import IsDetectiveBoardOwner
from investigation.models import DetectiveBoard
from accounts.models import User
from django.utils import timezone
from datetime import timedelta


case_list_example = {
                "id": 12,
                "title": "Bank Robbery",
                "description": "Armed robbery at city branch.",
                "crime_datetime": "2026-02-19T10:30:00Z",
                "crime_level": "CR",
                "status": "open",
                "lead_detective": "Alex Carter",
                "supervisor": "Sam Lee",
                "your_role": "SUPERVISOR",
                "witnesses": [
                    {
                        "id": 2,
                        "first_name": "User",
                        "last_name": "One",
                        "national_id": "2222222222",
                        "phone_number": "+989121234568"
                    }
                ],
                "complainants": [
                    {
                        "id": 2,
                        "first_name": "User",
                        "last_name": "One",
                        "national_id": "2222222222",
                        "phone_number": "+989121234568"
                    }
                ],
                "suspects": [
                    {
                        "id": 2,
                        "first_name": "User",
                        "last_name": "One",
                        "national_id": "2222222222",
                        "suspect_link": 1,
                        "supervisor_score": 1,
                        "detective_score": 1,
                        "status": "WANTED",
                        "phone_number": "+989121234568"
                    },
                    {
                        "id": 3,
                        "first_name": "User",
                        "last_name": "Three",
                        "national_id": "3333333333",
                        "suspect_link": 2,
                        "supervisor_score": 1,
                        "detective_score": 1,
                        "status": "WANTED",
                        "phone_number": "+989121234569"
                    }
                ],
            }

@extend_schema(
    summary="List cases (full details)",
    description=(
        "Returns full case details for users who are assigned as lead detective/supervisor "
        "or have `cases.view_case`. "
        "Cases where the caller is a complainant are excluded from this endpoint."
    ),
    responses=CaseListSerializer(many=True),
    examples=[
        OpenApiExample(
            name="Full case list response",
            response_only=True,
            status_codes=["200"],
            value=case_list_example,
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
        if user.has_perm("cases.view_case"):
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
                "complainants": [
                    {
                        "id": 2,
                        "first_name": "User",
                        "last_name": "One",
                        "national_id": "2222222222",
                        "phone_number": "+989121234568"
                    }
                ]
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
            "or have `cases.view_case`. "
            "Complainants are blocked from this endpoint even if they have `cases.view_case`."
        ),
        responses=CaseListSerializer,
        examples=[
            OpenApiExample(
                name="Full case list response",
                response_only=True,
                status_codes=["200"],
                value=case_list_example,
            ),
        ],
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
                    "witnesses_national_ids": ["1111111111", "2222222222"],
                    "suspects": [
                        {"suspect_link": 9, "score": 8},
                        {"suspect_link": 10, "supervisor_score":5, "status":"ARRESTED"}
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
            return case

        case = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        complainant_ids = {complainant.id for complainant in case.complainants.all()}
        if user.id in complainant_ids:
            raise PermissionDenied("Complainants cannot access full case details.")

        if user.has_perm("cases.view_case"):
            return case

        if case.lead_detective_id == user.id or case.supervisor_id == user.id:
            return case

        raise PermissionDenied("Only assigned detective/supervisor or users with view_case can access this case.")


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
                    child=serializers.ChoiceField(choices=["ASSIGNED_CASES", "COMPLAINANT_CASES", "AUTOPSY", "PROFILE"]),
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

        if user.has_perm("cases.investigate_on_case") or user.has_perm("cases.supervise_case") or user.has_perm("cases.view_case"):
            items.append("ASSIGNED_CASES")

        if user.has_perm("evidence.can_approve_bioevidence"):
            items.append("AUTOPSY")

        if user.has_perm("case.jury_case"):
            items.append("JURY")

        items.append("COMPLAINANT_CASES")
        items.append("PROFILE")

        return Response({"modules":items})
    
class GetTrialCases(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseListSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.has_perm("cases.jury_case"):
            raise PermissionDenied("Only users with jury permission can access trial cases.")

        return (
            Case.objects
            .filter(status=Case.Status.TRIAL)
            .select_related("lead_detective", "supervisor")
            .prefetch_related("complainants", "witnesses", "suspect_links__user")
            .order_by("-id")
        )


@extend_schema(
    summary="List most wanted suspects",
    description=(
        "Returns a list of suspects ordered by a 'wanted score' calculated based on the severity of their alleged crimes and the duration they've been suspects. "
        "Only suspects who have been investigated for at least 30 days are included. "
    ),
    responses=MostWantedSerializer(many=True),
    request=None,
    examples=[
        OpenApiExample(
            name="Most wanted suspects response",
            response_only=True,
            status_codes=["200"],
            value=[
                {
                    "id": 2,
                    "username": "userone",
                    "first_name": "User",
                    "last_name": "One",
                    "reward_amount": 40000000,
                    "wanted_score": 2
                },
                {
                    "id": 3,
                    "username": "usertwo",
                    "first_name": "User",
                    "last_name": "Two",
                    "reward_amount": 20000000,
                    "wanted_score": 1
                }
            ],
        )
    ]
)
class MostWanted(generics.ListAPIView):
    serializer_class = MostWantedSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        from django.db.models import (ExpressionWrapper, F, Max, DurationField,Case as DBCase,When, Value,IntegerField)
        from django.db.models.functions import Now, Coalesce, Extract
        from .models import Case
        threshold = timezone.now() - timedelta(days=30)
        users = User.objects.filter(
            case_suspect_links__started_at__lt=threshold,
        ).annotate(
            max_duration=Max(
                ExpressionWrapper(
                    Coalesce(F('case_suspect_links__ended_at'), Now()) - F('case_suspect_links__started_at'),
                    output_field=DurationField()
                )
            ),
            max_degree=Max(
                DBCase(
                    When(case_suspect_links__case__crime_level=Case.CrimeLevel.LEVEL_1, then=Value(1)),
                    When(case_suspect_links__case__crime_level=Case.CrimeLevel.LEVEL_2, then=Value(2)),
                    When(case_suspect_links__case__crime_level=Case.CrimeLevel.LEVEL_3, then=Value(3)),
                    When(case_suspect_links__case__crime_level=Case.CrimeLevel.CRITICAL, then=Value(4)),
                    output_field=IntegerField(),
                )
            )
        )

        users_list = list(users)
        for user in users_list:
            max_days = user.max_duration.days if user.max_duration else 0
            degree = user.max_degree if user.max_degree else 0
            user.wanted_score = max_days * degree

        
        users_list.sort(key=lambda u: u.wanted_score, reverse=True)
        return users_list

class CaseVerdictView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        case: Case = get_object_or_404(Case, pk=pk)
        user: User = request.user
        if not user.has_perm("cases.jury_case"):
            raise PermissionDenied("Only users with jury permission can submit verdicts.")
        
        users = case.suspects.filter(case_suspect_links__case=case, case_suspect_links__guilt_status=CaseSuspectLink.SuspectGuiltStatus.GUILTY)
        verdicts = request.data.get("verdicts")
        if verdicts is None or not isinstance(verdicts, list):
            raise ValueError("verdicts field is required and should be a list of verdict objects.")
        
        for verdict in verdicts:
            user_id = verdict.get("user_id")
            
            if not User.objects.filter(id=user_id, case_suspect_links__case=case).exists():
                raise ValueError(f"User with id {user_id} is not a suspect in this case.")
            
            user = User.objects.get(id=user_id)
            suspect_link = CaseSuspectLink.objects.get(user=user, case=case)
            guilt_status = verdict.get("guilt_status")
            title = verdict.get("title")
            description = verdict.get("description")


            if guilt_status not in CaseSuspectLink.SuspectGuiltStatus.values or guilt_status == CaseSuspectLink.SuspectGuiltStatus.PENDING_ASSESSMENT:
                raise ValueError(f"Invalid guilt_status: {guilt_status} should be one of 'GUILTY' or 'CLEARED'.")
            
            if title is None or description is None:
                raise ValueError("Both title and description are required for the verdict.")


            suspect_link.guilt_status = guilt_status
            suspect_link.verdict_title = title
            suspect_link.verdict_description = description
            suspect_link.ended_at = timezone.now()
            suspect_link.save()
        
        return Response({"detail": "Verdicts submitted successfully."}, status=status.HTTP_200_OK)
