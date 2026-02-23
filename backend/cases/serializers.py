from typing import Any

from rest_framework import serializers
from .models import Complaint, CrimeScene, Case, CaseSubmissionLink, CaseSuspectLink, InvestigationResults
from accounts.models import User
from accounts.serializers.fields import NationalIDField, PhoneNumberField
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema_field

# ---------------------------------------------------------------------
# complaint
# ---------------------------------------------------------------------

class ComplaintSerializer(serializers.ModelSerializer):
    complainant_national_ids = serializers.SerializerMethodField(
        help_text="National IDs of complainants attached to this complaint.",
    )

    class Meta:
        model = Complaint
        fields = ["id", "title", "description", "crime_datetime", "complainant_national_ids"]

    def validate_complainant_national_ids(self, national_ids):
        seen = set()
        deduped = []
        for nid in national_ids:
            if nid not in seen:
                seen.add(nid)
                deduped.append(nid)
        return deduped

    def get_complainant_national_ids(self, obj) -> list[str]:
        return list(obj.complainants.values_list("national_id", flat=True))

    def _get_actor(self) -> User:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError(
                {"non_field_errors": ["Authenticated request context is required."]}
            )
        return user

    def _resolve_complainants(self, national_ids: list[str], actor: User) -> list[User]:
        users_by_nid = {
            user.national_id: user
            for user in User.objects.filter(national_id__in=national_ids)
        }

        ordered_users = []
        seen_ids = set()
        for nid in national_ids:
            user = users_by_nid.get(nid)
            if user and user.id not in seen_ids:
                ordered_users.append(user)
                seen_ids.add(user.id)

        if actor.id not in seen_ids:
            ordered_users.append(actor)

        return ordered_users

    def create(self, validated_data):
        actor = self._get_actor()
        national_ids = validated_data.pop("complainant_national_ids", [])

        complaint = Complaint.objects.create(**validated_data)

        complaint.complainants.set(self._resolve_complainants(national_ids, actor))
        return complaint

    def update(self, instance, validated_data):
        actor = self._get_actor()
        national_ids = validated_data.pop("complainant_national_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if national_ids is not None:
            instance.complainants.set(self._resolve_complainants(national_ids, actor))

        instance.save()
        return instance


class ComplaintPayloadSerializer(ComplaintSerializer):
    complainant_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        required=False,
        help_text=(
            "Optional list of complainants' national IDs. "
            "If omitted, the authenticated user is added as a complainant."
        ),
    )

# ---------------------------------------------------------------------
# Crime scene
# ---------------------------------------------------------------------

class WitnessItemSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(
        help_text="Witness phone number in Iranian format.",
    )
    national_id = NationalIDField(
        should_exist=True,
        help_text="National ID of an existing user who is a witness.",
    )

class CrimeSceneSerializer(serializers.ModelSerializer):
    witnesses = WitnessItemSerializer(
        many=True,
        required=True,
        help_text="Witnesses linked to this crime scene.",
    )

    class Meta:
        model = CrimeScene
        fields = ["id", "title", "description", "witnesses", "crime_datetime"]
    
    def validate_witnesses(self, witnesses):
        counts = {}
        for w in witnesses:
            nid = w.get("national_id")
            counts[nid] = counts.get(nid, 0) + 1

        errors = [{} for _ in witnesses]
        has_errors = False
        for i, w in enumerate(witnesses):
            nid = w.get("national_id")
            if counts.get(nid, 0) > 1:
                errors[i].setdefault("national_id", []).append(
                    f"Duplicate national_id: {nid}."
                )
                has_errors = True

        if has_errors:
            raise serializers.ValidationError(errors)

        return witnesses

    def create(self, validated_data):
        return super().create(validated_data)

# ---------------------------------------------------------------------
# Case staffing
# ---------------------------------------------------------------------

class CaseStaffingSubmissionPayloadSerializer(serializers.ModelSerializer):
    lead_detective = serializers.SerializerMethodField()
    supervisor = serializers.SerializerMethodField()
    origin_submission_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Case
        fields = [
            "id", "title", "description", "crime_datetime", "crime_level",
            "lead_detective", "supervisor", "origin_submission_id"
        ]
        read_only_fields = fields

    def get_lead_detective(self, obj) -> str:
        return "Not Assigned" if obj.lead_detective is None else (obj.lead_detective.first_name + " " + obj.lead_detective.last_name)

    def get_supervisor(self, obj) -> str:
        return "Not Assigned" if obj.supervisor is None else (obj.supervisor.first_name + " " + obj.supervisor.last_name)
    
    def get_origin_submission_id(self, obj:Case) -> int:
        link = obj.submission_links.filter(
            relation_type=CaseSubmissionLink.RelationType.ORIGIN
        ).select_related("submission").first()

        if not link:
            return None

        return link.submission.id

# ---------------------------------------------------------------------
# Case list
# ---------------------------------------------------------------------

class UserBriefInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "national_id"]
        read_only_fields = fields


class SuspectInfoSerializer(UserBriefInfoSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    national_id = serializers.CharField(source="user.national_id", read_only=True)
    suspect_link = serializers.IntegerField(source="id", read_only=True)
    supervisor_score = serializers.IntegerField(read_only=True)
    detective_score = serializers.IntegerField(read_only=True)
    status = serializers.CharField(source="user.status", read_only=True)

    class Meta:
        model = CaseSuspectLink
        fields = ["id", "first_name", "last_name", "national_id",
                   "suspect_link", "supervisor_score", "detective_score", "status"]
        read_only_fields = fields


class CaseListSerializer(serializers.ModelSerializer):
    lead_detective = serializers.SerializerMethodField()
    supervisor = serializers.SerializerMethodField()
    your_role = serializers.SerializerMethodField()
    complainants = UserBriefInfoSerializer(
        source="complainants.all",
        many=True,
        read_only=True,
    )
    suspects = SuspectInfoSerializer(
        source="suspect_links.all",
        many=True,
        read_only=True,
    )
    
    class Meta:
        model = Case
        fields = [
            "id",
            "title",
            "description",
            "crime_datetime",
            "crime_level",
            "status",
            "witnesses",
            "lead_detective",
            "supervisor",
            "complainants",
            "suspects",
            "your_role"
        ]
        read_only_fields = fields

    def get_lead_detective(self, obj) -> str:
        if obj.lead_detective is None:
            return "Not Assigned"
        return f"{obj.lead_detective.first_name} {obj.lead_detective.last_name}".strip()

    def get_supervisor(self, obj) -> str:
        if obj.supervisor is None:
            return "Not Assigned"
        return f"{obj.supervisor.first_name} {obj.supervisor.last_name}".strip()

    @extend_schema_field(
        serializers.ChoiceField(choices=["DETECTIVE", "SUPERVISOR"], allow_null=True)
    )
    def get_your_role(self, obj) -> str | None:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        if obj.lead_detective_id == user.id:
            return "DETECTIVE"
        if obj.supervisor_id == user.id:
            return "SUPERVISOR"
        return None

# ---------------------------------------------------------------------
# Investigation results
# ---------------------------------------------------------------------

class InvestigationResultsApprovalPayloadSerializer(serializers.Serializer):
    case_id = serializers.IntegerField(min_value=1, required=True)

class SuspectCriminalRecordItemSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Case
        fields = ["case_id", "title", "description", "crime_datetime", "status"]
        read_only_fields = fields


class InvestigationSuspectSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    criminal_record = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["name", "national_id", "criminal_record"]
        read_only_fields = fields

    def get_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_criminal_record(self, obj: User) -> SuspectCriminalRecordItemSerializer:
        cases = obj.suspect_cases.all().order_by("id")
        return SuspectCriminalRecordItemSerializer(cases, many=True, context=self.context).data

class InvestigationResultsSubmissionSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(
        queryset=Case.objects.all(),
        write_only=True,
        help_text="Case ID for which investigation results are submitted.",
    )
    case_details = CaseListSerializer(source="case", read_only=True)
    suggested_suspects_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        write_only=True,
        help_text="List of suggested suspects national IDs.",
    )
    suggested_suspects = InvestigationSuspectSerializer(
        source="suspects",
        many=True,
        read_only=True,
    )

    class Meta:
        model = InvestigationResults
        fields = [
            "case",
            "suggested_suspects_national_ids",
            "case_details",
            "suggested_suspects",
        ]
        read_only_fields = ["case_details", "suggested_suspects"]

    def validate_suggested_suspects_national_ids(self, national_ids: list[str]) -> list[str]:
        seen = set()
        deduped = []
        for nid in national_ids:
            if nid not in seen:
                seen.add(nid)
                deduped.append(nid)
        return deduped

    def _resolve_suspects(self, national_ids: list[str]) -> list[User]:
        users_by_nid = {
            user.national_id: user
            for user in User.objects.filter(national_id__in=national_ids)
        }
        return [users_by_nid[nid] for nid in national_ids if nid in users_by_nid]

    def create(self, validated_data):
        national_ids = validated_data.pop("suggested_suspects_national_ids", [])
        suspects = self._resolve_suspects(national_ids)

        investigation_results = super().create(validated_data)
        investigation_results.suggested_suspects.set(suspects)
        return investigation_results

# ---------------------------------------------------------------------
# Complainant cases
# ---------------------------------------------------------------------

class ComplainantCaseListSerializer(serializers.ModelSerializer):
    complainant_national_ids = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "title",
            "crime_datetime",
            "status",
            "complainant_national_ids"
        ]

    def get_complainant_national_ids(self, obj) -> list[str]:
        return list(obj.complainants.values_list("national_id", flat=True))

# ---------------------------------------------------------------------
# Case update
# ---------------------------------------------------------------------

class IndexedErrorsListSerializer(serializers.ListSerializer):
    def run_validation(self, data=serializers.empty):
        try:
            return super().run_validation(data)
        except serializers.ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, list):
                indexed_errors = {}
                for i, item in enumerate(detail):
                    if item in (None, {}, []):
                        continue
                    indexed_errors[str(i)] = item
                raise serializers.ValidationError(indexed_errors)
            raise


class CaseUpdateWitnessItemSerializer(WitnessItemSerializer):
    class Meta:
        list_serializer_class = IndexedErrorsListSerializer


class SuspectUpdateSerilizer(serializers.Serializer):
    suspect_link = serializers.PrimaryKeyRelatedField(
        queryset=CaseSuspectLink.objects.all(),
        write_only=True
    )
    supervisor_score = serializers.IntegerField(
        write_only=True,
        required=False
    )
    lead_detective_score = serializers.IntegerField(
        write_only=True,
        required=False
    )
    score = serializers.IntegerField(
        write_only=True,
        required=False
    )
    status = serializers.ChoiceField(
        choices=User.Status.choices,
        required=False,
        write_only=True
    )

    def validate(self, attrs):
        suspect_link: CaseSuspectLink = attrs["suspect_link"]
        case = suspect_link.case
        user: User = self.context["request"].user

        changing_score:bool = ("lead_detective_score" in attrs) or \
                                ("supervisor_score" in attrs) or \
                                ("score" in attrs)

        if (suspect_link.user.status == suspect_link.user.Status.WANTED) and (changing_score):
            raise serializers.ValidationError({"suspect_link" : "suspect is wanted and not interogated yet"})
        
        if (case.lead_detective.id != user.id) and (case.supervisor.id != user.id):
            raise PermissionDenied("You should be the detective / supervisor of the case")

        if "supervisor_score" in attrs and case.supervisor_id != user.id:
            raise serializers.ValidationError(
                {"score": "Only the case supervisor can set this field."}
            )
        
        if "lead_detective_score" in attrs and case.lead_detective_id != user.id:
            raise serializers.ValidationError(
                {"score": "Only the lead detective of the case can set this field."}
            )
        
        return attrs
    
    def validate_lead_detective_score(self, value: int):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("should be between 1 and 10")
        return value

    def validate_supervisor_score(self, value: int):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("should be between 1 and 10")
        return value

    def validate_score(self, value: int):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("should be between 1 and 10")
        return value

    class Meta:
        list_serializer_class = IndexedErrorsListSerializer


class CaseUpdateSerializer(serializers.ModelSerializer):
    complainant_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        required=False,
        write_only=True,
        help_text="List of complainants national IDs.",
    )
    witnesses = CaseUpdateWitnessItemSerializer(
        many=True,
        required=False,
        write_only=True,
        help_text="Witnesses linked to this case.",
    )
    suspects = SuspectUpdateSerilizer(
        many=True,
        required=False,
        write_only=True
    )

    class Meta:
        model = Case
        fields = [
            "title",
            "description",
            "crime_level",
            "complainant_national_ids",
            "witnesses",
            "suspects"
        ]

    def get_complainant_national_ids(self, obj):
        return list(obj.complainants.values_list("national_id", flat=True))

    def validate_complainant_national_ids(self, national_ids):
        seen = set()
        deduped = []
        for nid in national_ids:
            if nid not in seen:
                seen.add(nid)
                deduped.append(nid)
        return deduped

    def validate_witnesses(self, witnesses):
        counts = {}
        for w in witnesses:
            nid = w.get("national_id")
            counts[nid] = counts.get(nid, 0) + 1

        indexed_errors = {}
        for i, w in enumerate(witnesses):
            nid = w.get("national_id")
            if counts.get(nid, 0) > 1:
                indexed_errors[str(i)] = {
                    "national_id": [f"Duplicate national_id: {nid}."]
                }

        if indexed_errors:
            raise serializers.ValidationError(indexed_errors)

        return witnesses
    
    def validate_suspects(self, suspects):
        counts = {}
        for s in suspects:
            sid = s.get("suspect_link").pk
            counts[sid] = counts.get(sid, 0) + 1

        indexed_errors = {}
        case_id = getattr(self.instance, "id", None)

        case: Case = self.instance
        if case.status != case.Status.INTEROGATING_SUSPECTS:
            raise serializers.ValidationError("the case is in open investigation state")

        for i, s in enumerate(suspects):
            link: CaseSuspectLink = s.get("suspect_link")
            sid = link.pk
            if counts.get(sid, 0) > 1:
                indexed_errors[str(i)] = {
                    "suspect_link": [f"Duplicate suspect_link: {sid}."]
                }
            if case_id is not None and link.case_id != case_id:
                indexed_errors.setdefault(str(i), {}).setdefault("suspect_link", []).append(
                    f"Suspect link {sid} does not belong to this case."
                )

        if indexed_errors:
            raise serializers.ValidationError(indexed_errors)

        return suspects

    def update(self, instance, validated_data):
        complainant_national_ids = validated_data.pop("complainant_national_ids", None)
        suspects = validated_data.pop("suspects", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if complainant_national_ids is not None:
            users_by_nid = {
                user.national_id: user
                for user in User.objects.filter(national_id__in=complainant_national_ids)
            }
            ordered_users = [users_by_nid[nid] for nid in complainant_national_ids if nid in users_by_nid]
            instance.complainants.set(ordered_users)

        if suspects is not None:
            for s in suspects:
                link: CaseSuspectLink = s["suspect_link"]

                if "supervisor_score" in s:
                    link.supervisor_score = s["supervisor_score"]

                if "lead_detective_score" in s:
                    link.detective_score = s["lead_detective_score"]
                elif "score" in s:
                    user: User = self.context["request"].user
                    if instance.supervisor_id == user.id:
                        link.supervisor_score = s["score"]
                    if instance.lead_detective_id == user.id:
                        link.detective_score = s["score"]
                
                if "status" in s:
                    link.user.status = s["status"]
                    link.user.save()
                link.save()

        instance.save()

        return instance

# ---------------------------------------------------------------------
# Case submisions
# ---------------------------------------------------------------------

class SubmissionSerializer(serializers.Serializer):
    def __new__(cls, *args, **kwargs):
        # Avoid importing submissions serializers at module load time.
        from submissions.serializers.classes import SubmissionSerializer as _SubmissionSerializer

        return _SubmissionSerializer(*args, **kwargs)


class CaseLinkedSubmissionSerializer(serializers.ModelSerializer):
    relation = serializers.CharField(source="relation_type", read_only=True)
    submission = serializers.SerializerMethodField()

    @extend_schema_field(SubmissionSerializer)
    def get_submission(self, obj: CaseSubmissionLink) -> dict[str, Any]:
        return SubmissionSerializer(obj.submission, context=self.context).data

    class Meta:
        model = CaseSubmissionLink
        fields = ["relation", "submission"]
        read_only_fields = fields

# ---------------------------------------------------------------------
# Case submisions
# ---------------------------------------------------------------------

class CaseChargesSubmissionSerializer(CaseListSerializer):
    case_id = serializers.PrimaryKeyRelatedField(
        queryset=Case.objects.all(),
        write_only=True
    )

    class Meta(CaseListSerializer.Meta):
        fields = CaseListSerializer.Meta.fields + ["case_id"]