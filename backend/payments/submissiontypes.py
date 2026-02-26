from submissions.submissiontypes.classes import BaseSubmissionType
from submissions.models import Submission, SubmissionAction, SubmissionStage, SubmissionActionType, SubmissionStatus
from .models import BailRequest
from accounts.models import User
from .serializers import BailRequestSerializer
from rest_framework.exceptions import ValidationError



class BailRequestSubmissionType(BaseSubmissionType["BailRequest"]):
    type_key = "BAIL_REQUEST"
    display_name = "Bail Request"
    model_class = BailRequest
    serializer_class = BailRequestSerializer
    create_permissions = []
    api_request_schema = None
    api_request_payload_example = None
    api_response_target_example = None

    @classmethod
    def on_submit(cls, submission):
        bail = cls.get_object(submission.object_id)
        bail.requested_by = submission.created_by
        bail.save()

        SubmissionStage.objects.create(
            submission=submission,
            target_permission="payments.can_approve_bail_request",
            order=0,
            allowed_actions=[SubmissionActionType.ACCEPT, SubmissionActionType.REJECT]
        )
        submission.current_stage = 0
        submission.save()

    @classmethod
    def validate_submission_action_payload(cls, submission, action_type, payload, context, **kwargs):
        if action_type == SubmissionActionType.ACCEPT:
            if "amount" not in payload:
                raise ValidationError({"payload": {"amount": "This field is required."}})
        
    @classmethod
    def handle_submission_action(cls, submission, action, context, **kwargs):
        if submission.current_stage == 0:
            if action.action_type == SubmissionActionType.ACCEPT:
                bail = cls.get_object(submission.object_id)
                bail.status = BailRequest.Status.APPROVED
                bail.amount = action.payload.get("amount")
                bail.save()
                submission.status = SubmissionStatus.ACCEPTED
                submission.save()
            elif action.action_type == SubmissionActionType.REJECT:
                bail = cls.get_object(submission.object_id)
                bail.status = BailRequest.Status.REJECTED
                bail.save()
                submission.status = SubmissionStatus.REJECTED
                submission.save()
    @classmethod
    def can_submit(cls, user: User, obj):
        return user.status == User.Status.ARRESTED and not BailRequest.objects.filter(requested_by=user, status=BailRequest.Status.PENDING).exists()
