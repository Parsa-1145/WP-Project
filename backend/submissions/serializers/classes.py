from rest_framework import serializers
from submissions import models
from submissions.submissiontypes.registry import get_submission_type
from django.core.exceptions import ValidationError, PermissionDenied
from submissions.models import Submission, SubmissionStatus, SubmissionEvent, SubmissionEventType, SubmissionStage
from submissions.submissiontypes.classes import BaseSubmissionType

class SubmissionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model=SubmissionEvent
        fields=["id", "event_type", "message", "created_at", "actor"]

class SubmissionStageSerializer(serializers.ModelSerializer):
    class Meta:
        model=SubmissionStage
        fields=["id", "target_permissions", "target_user", "order"]

class SubmissionSerializer(serializers.ModelSerializer):
    payload = serializers.JSONField(write_only=True)
    submission_type = serializers.CharField()
    
    target = serializers.SerializerMethodField(read_only=True)
    events = SubmissionEventSerializer(many=True, read_only=True)
    stages = SubmissionStageSerializer(many=True, read_only=True)

    class Meta:
        model=models.Submission
        fields = [
            "id", "submission_type", "payload", "status",
            "target", "events", "current_stage", "stages",
        ]
        read_only_fields = ["status", "target", "events", "current_stage", "stages"]

    def get_target(self, obj):
        submission_type_cls = get_submission_type(obj.submission_type)
        try:
            target_obj = submission_type_cls.get_object(obj.object_id)
        except submission_type_cls.model_class.DoesNotExist:
            return None
        return submission_type_cls.serializer_class(target_obj, context=self.context).data

    def validate(self, attrs):
        type_key = attrs.get("submission_type")
        payload = attrs.get("payload") or {}
        
        try:
            submission_type_cls = get_submission_type(type_key)
        except KeyError:
            raise ValidationError({"submission_type": "Unsupported submission type: " + type_key})
        
        
        try:
            payload_serializer = submission_type_cls.validate_submission_data(
                data=payload,
                context=self.context,
            )
        except Exception as e:
            raise serializers.ValidationError({"payload": [e.detail]}) # TODO dog shit

        user = self.context["request"].user
        if not submission_type_cls.does_user_have_access(user):
            raise PermissionDenied()
    

        attrs["_submission_type_cls"] = submission_type_cls
        attrs["_payload_serializer"] = payload_serializer
        attrs["creator"] = user
        return attrs
    
    def create(self, validated_data):
        submission_type_cls:BaseSubmissionType = validated_data.pop("_submission_type_cls")
        payload_serializer = validated_data.pop("_payload_serializer")

        target_obj = payload_serializer.save()
        submission_type=validated_data["submission_type"]

        submission = Submission.objects.create(
            submission_type=submission_type,
            object_id=target_obj.pk,
            status=SubmissionStatus.PENDING,
        )

        submission_type_cls.on_submit(submission=submission)

        submit_event = SubmissionEvent.objects.create(
            submission = submission,
            event_type = SubmissionEventType.SUBMIT,
            message = "Request created",
            actor = validated_data["creator"]
        )

        return submission
    
