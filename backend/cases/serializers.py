from rest_framework import serializers
from .models import Complaint, CrimeScene, Case, CaseSubmissionLink, CaseSuspectLink
from accounts.models import User
from accounts.serializers.fields import NationalIDField, PhoneNumberField
from rest_framework.exceptions import PermissionDenied

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

    def get_lead_detective(self, obj):
        return "Not Assigned" if obj.lead_detective is None else (obj.lead_detective.first_name + " " + obj.lead_detective.last_name)

    def get_supervisor(self, obj):
        return "Not Assigned" if obj.supervisor is None else (obj.supervisor.first_name + " " + obj.supervisor.last_name)
    
    def get_origin_submission_id(self, obj:Case):
        link = obj.submission_links.filter(
            relation_type=CaseSubmissionLink.RelationType.ORIGIN
        ).select_related("submission").first()

        if not link:
            return None

        return link.submission.id

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

    def get_criminal_record(self, obj: User):
        cases = obj.suspect_cases.all().order_by("id")
        return SuspectCriminalRecordItemSerializer(cases, many=True, context=self.context).data



class InvestigationResultsApprovalTargetSerializer(serializers.ModelSerializer):
    suspects = InvestigationSuspectSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = ["id", "title", "description", "crime_datetime", "crime_level", "suspects"]
        read_only_fields = fields

# ---------------------------------------------------------------------
# Case list
# ---------------------------------------------------------------------

class CaseListSerializer(serializers.ModelSerializer):
    lead_detective = serializers.SerializerMethodField()
    supervisor = serializers.SerializerMethodField()
    complainant_national_ids = serializers.SerializerMethodField()
    suspects_national_ids = serializers.SerializerMethodField()
    
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
            "complainant_national_ids",
            "suspects_national_ids"
        ]

    def get_lead_detective(self, obj) -> str | None:
        if obj.lead_detective is None:
            return "Not Assigned"
        return f"{obj.lead_detective.first_name} {obj.lead_detective.last_name}".strip()

    def get_supervisor(self, obj) -> str | None:
        if obj.supervisor is None:
            return "Not Assigned"
        return f"{obj.supervisor.first_name} {obj.supervisor.last_name}".strip()

    def get_complainant_national_ids(self, obj) -> list[str]:
        return list(obj.complainants.values_list("national_id", flat=True))
    def get_suspects_national_ids(self, obj:Case) -> list[str]:
        return list(obj.suspects.values_list("national_id", flat=True))

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

class CaseUpdateSerializer(serializers.ModelSerializer):
    complainant_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        required=False,
        help_text="List of complainants national IDs.",
    )
    suspects_national_ids = serializers.ListField(
        child=NationalIDField(should_exist=True),
        required=False,
        help_text="List of suspects national IDs.",
    )
    witnesses = WitnessItemSerializer(
        many=True,
        required=False,
        help_text="Witnesses linked to this case.",
    )

    class Meta:
        model = Case
        fields = [
            "id",
            "title",
            "description",
            "complainant_national_ids",
            "suspects_national_ids",
            "witnesses"
        ]
        read_only_fields = ["id"]

    def get_complainant_national_ids(self, obj):
        return list(obj.complainants.values_list("national_id", flat=True))
    def get_suspects_national_ids(self, obj):
        return list(obj.suspects.values_list("national_id", flat=True))
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["complainant_national_ids"] = self.get_complainant_national_ids(instance)
        data["suspects_national_ids"] = self.get_suspects_national_ids(instance)
        return data

    def validate_complainant_national_ids(self, national_ids):
        seen = set()
        deduped = []
        for nid in national_ids:
            if nid not in seen:
                seen.add(nid)
                deduped.append(nid)
        return deduped
    
    def validate_suspects_national_ids(self, national_ids):
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

    def update(self, instance, validated_data):
        complainant_national_ids = validated_data.pop("complainant_national_ids", None)
        suspects_national_ids = validated_data.pop("suspects_national_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if complainant_national_ids is not None:
            users_by_nid = {
                user.national_id: user
                for user in User.objects.filter(national_id__in=complainant_national_ids)
            }
            ordered_users = [users_by_nid[nid] for nid in complainant_national_ids if nid in users_by_nid]
            instance.complainants.set(ordered_users)

        if suspects_national_ids is not None:
            users_by_nid = {
                user.national_id: user
                for user in User.objects.filter(national_id__in=suspects_national_ids)
            }
            ordered_users = [users_by_nid[nid] for nid in suspects_national_ids if nid in users_by_nid]
            instance.suspects.set(ordered_users)

        return instance

# ---------------------------------------------------------------------
# Case submisions
# ---------------------------------------------------------------------

class CaseLinkedSubmissionSerializer(serializers.ModelSerializer):
    relation = serializers.CharField(source="relation_type", read_only=True)
    submission = serializers.SerializerMethodField()

    def get_submission(self, obj):
        from submissions.serializers.classes import SubmissionSerializer
        return SubmissionSerializer(obj.submission, context=self.context).data

    class Meta:
        model = CaseSubmissionLink
        fields = ["relation", "submission"]