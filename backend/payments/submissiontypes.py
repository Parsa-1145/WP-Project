from submissions.submissiontypes.classes import BaseSubmissionType
from submissions.models import Submission, SubmissionAction, SubmissionStage, SubmissionActionType, SubmissionStatus
from .models import BailRequest


class BailRequestSubmissionType(BaseSubmissionType["BailRequest"]):
    type_key = "BAIL_REQUEST"
    display_name = "Bail Request"
    model_class = None
    serializer_class = None
    create_permissions = []
    api_schema = None
    api_payload_example = None
    api_response_target_example = None

    @classmethod
    def on_submit(cls, submission):
        cls.get_object(submission.object_id).user = submission.created_by

        SubmissionStage.objects.create(
            submission=submission,
            target_permission="finance.can_approve_bail_request",
            order=0,
            allowed_actions=[SubmissionActionType.ACCEPT, SubmissionActionType.REJECT]
        )
        submission.current_stage = 0
        submission.save()

    @classmethod
    def handle_submission_action(cls, submission, action, context, **kwargs):
        if submission.current_stage == 0:
            if action.action_type == SubmissionActionType.ACCEPT:
                bail = cls.get_object(submission.object_id)
                bail.status = BailRequest.Status.APPROVED
                bail.amount = action.payload.amount
                submission.status = SubmissionStatus.ACCEPTED
                submission.save()
            elif action.action_type == SubmissionActionType.REJECT:
                cls.get_object(submission.object_id).status = BailRequest.Status.REJECTED
                submission.status = SubmissionStatus.REJECTED
                submission.save()
