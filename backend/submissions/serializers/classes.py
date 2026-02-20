from rest_framework import serializers
from submissions import models
from submissions.submissiontypes.registry import get_submission_type
from django.core.exceptions import ValidationError, PermissionDenied
from submissions.models import Submission, SubmissionStatus, SubmissionAction, SubmissionActionType, SubmissionStage
from submissions.submissiontypes.classes import BaseSubmissionType
from submissions.submissiontypes.registry import get_submission_type
from accounts.models import User
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, PolymorphicProxySerializer
from submissions.service import create_submission

# ---------------------------------------------------------------------
# SubmissionActionSerializer
# ---------------------------------------------------------------------

class SubmissionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAction
        fields = ["id", "submission", "action_type", "payload", "created_by", "created_at"]
        read_only_fields = ["id", "submission", "created_by", "created_at"]

    submission = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate(self, attrs):
        submission: Submission = self.context.get("submission") or getattr(self.instance, "submission", None)
        if submission is None:
            raise serializers.ValidationError({"submission": "This field is required."})
        
        user: User = self.context["request"].user

        submission_type_cls = get_submission_type(submission.submission_type)  # FIX: use instance, not model class

        stage = SubmissionStage.objects.filter(
            submission=submission,
            order=submission.current_stage,
        ).first()

        if stage is None:
            raise serializers.ValidationError({"submission": "Submission stage corrupted"})

        if not (((stage.target_user is not None) and stage.target_user == user) 
                or ((stage.target_permission is not None) and user.has_perm(stage.target_permission))):
            raise PermissionDenied()

        action_type: SubmissionActionType = attrs["action_type"]

        allowed = stage.allowed_actions or []

        if action_type not in allowed:
            raise serializers.ValidationError({
                "action_type": f"Action type not allowed at this stage. allowed actions: {allowed}"
            })
        
        payload = attrs["payload"]

        if action_type == SubmissionActionType.REJECT:
            message = payload.get("message")
            if not message:
                raise serializers.ValidationError({
                    "payload": {
                        "message": ["Rejection message required"]
                    }
                })
            
        if action_type ==SubmissionActionType.RESUBMIT:
            try:
                submission_type_cls.validate_submission_data(payload, self.context)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    "payload": e.detail
                })
            except ValidationError as e:
                raise serializers.ValidationError({
                    "payload": e.message
                })
            
        

        attrs["created_by"] = user
        attrs["submission"] = submission
        return attrs

# ---------------------------------------------------------------------
# SubmissionStageSerializer
# ---------------------------------------------------------------------

class SubmissionStageSerializer(serializers.ModelSerializer):
    class Meta:
        model=SubmissionStage
        fields=["allowed_actions", "prompt"]

# ---------------------------------------------------------------------
# SubmissionSerializer
# ---------------------------------------------------------------------
def submission_target_schema():
    from submissions.submissiontypes.registry import SUBMISSION_TYPES

    return PolymorphicProxySerializer(
        component_name="SubmissionTarget",
        serializers=[
            st_cls.serializer_class
            for st_cls in SUBMISSION_TYPES.values()
            if st_cls.serializer_class is not None
        ],
        resource_type_field_name=None,
    )
@extend_schema_serializer(
    component_name="Submission",
    description="Request / Response body for creating a submission action."
)
class SubmissionSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.Submission
        fields = [
            "id", "submission_type", "payload", "status",
            "target", "actions_history", "available_actions", "action_prompt", "created_by", "created_at"
        ]
        read_only_fields = ["status", "target", "actions_history", "available_actions", "action_prompt", "created_by", "created_at"]

    payload = serializers.JSONField(
        write_only=True,
        help_text=(
            "Submission data. Shape depends on `submission_type` and is validated dynamically."
        ),
    )


    target = serializers.SerializerMethodField(
        read_only=True,
        help_text="Resolved target object (serialized) created/linked by this submission type. For example the created Complaint object",
    )

    actions_history = SubmissionActionSerializer(
        many=True,
        read_only=True,
        help_text="List of actions performed on this submission."
    )
    available_actions = serializers.SerializerMethodField(
        read_only=True,
        help_text="The available actions for the user to do"
    )
    action_prompt = serializers.SerializerMethodField(
        read_only=True,
        help_text="The prompt to be shown to the user"
    )

    @extend_schema_field(submission_target_schema())
    def get_target(self, obj):
        submission_type_cls = get_submission_type(obj.submission_type)
        try:
            target_obj = submission_type_cls.get_object(obj.object_id)
        except submission_type_cls.model_class.DoesNotExist:
            return None
        return submission_type_cls.serializer_class(target_obj, context=self.context).data
    
    def get_available_actions(self, obj:Submission):
        if not get_submission_type(obj.submission_type).can_user_do_action(obj, user=self.context["request"].user):
            return []
        
        
        stage = SubmissionStage.objects.filter(submission=obj, order=obj.current_stage).first()
        if stage is None:
            return []
        return [action for action in stage.allowed_actions]
    
    def get_action_prompt(self, obj:Submission):
        if not get_submission_type(obj.submission_type).can_user_do_action(obj, user=self.context["request"].user):
            return ""
        
        stage = SubmissionStage.objects.filter(submission=obj, order=obj.current_stage).first()
        if stage is None:
            return ""
        return stage.prompt

    def validate(self, attrs):
        type_key = attrs.get("submission_type")
        payload = attrs.get("payload") or {}

        try:
            submission_type_cls = get_submission_type(type_key)
        except KeyError:
            raise ValidationError({"submission_type": "Unsupported submission type: " + type_key})
        
        user = self.context["request"].user
        if not submission_type_cls.can_user_submit(user):
            raise PermissionDenied()
        
        if not submission_type_cls.serializer_class:
            raise ValidationError({"submission_type": "Unsupported submission type: " + type_key})

        try:
            submission_type_cls.validate_submission_data(
                data=payload,
                context=self.context,
            )
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"payload": e.detail})
        except ValidationError as e:
            if hasattr(e, "message_dict"):
                raise serializers.ValidationError({"payload": e.message_dict})
            raise serializers.ValidationError({"payload": e.messages})

        attrs["_submission_type_cls"] = submission_type_cls
        attrs["creator"] = user
        return attrs
    
    def create(self, validated_data):
        submission_type_cls:BaseSubmissionType = validated_data.pop("_submission_type_cls")

        target_obj = submission_type_cls.create_object(validated_data.pop("payload"))

        submission = create_submission(
            submission_type_cls=submission_type_cls,
            target=target_obj,
            created_by=validated_data["creator"]
        )

        return submission
    
