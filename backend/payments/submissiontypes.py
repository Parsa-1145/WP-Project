from submissions.submissiontypes.classes import BaseSubmissionType
from submissions.models import Submission, SubmissionAction, SubmissionStage, SubmissionActionType, SubmissionStatus
from .models import BailRequest, DataForReward, Reward
from accounts.models import User
from .serializers import BailRequestSerializer, DataForRewardSerializer
from rest_framework.exceptions import ValidationError
from cases.models import Case



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


class DataForRewardSubmissionType(BaseSubmissionType["DataForReward"]):
    type_key = "DATA_REWARD"
    display_name = "Data for reward"
    model_class = DataForReward
    serializer_class = DataForRewardSerializer

    @classmethod
    def on_submit(cls, submission):
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="payments.can_approve_data_reward",
            order=0,
            allowed_actions=[SubmissionActionType.SEND_TO_DETECTIVE, SubmissionActionType.REJECT]
        )
        submission.current_stage = 0
        submission.save()

    @classmethod
    def handle_submission_action(cls, submission: Submission, action, context, **kwargs):
        if submission.current_stage == 0:
            if action.action_type == SubmissionActionType.ACCEPT:
                case_id = action.payload.get("case_id")
                case: Case = Case.objects.get(id=case_id)
                lead_detective = case.lead_detective
                SubmissionStage.objects.create(
                    submission=submission,
                    target_user=lead_detective,
                    order=1,
                    allowed_actions=[SubmissionActionType.SET_REWARD, SubmissionActionType.REJECT]
                )
                submission.current_stage = 1
                submission.save()
            elif action.action_type == SubmissionActionType.REJECT:
                submission.status = SubmissionStatus.REJECTED
                submission.save()
        elif submission.current_stage == 1:
            if action.action_type == SubmissionActionType.ACCEPT:
                reward_amount = action.payload.get("reward_amount")
                reward = Reward.objects.create(
                    user=submission.created_by,
                    submission=submission,
                    amount=reward_amount,
                )
                data_for_reward = cls.get_object(submission.object_id)
                data_for_reward.reward = reward
                data_for_reward.save(update_fields=["reward"])
                submission.status = SubmissionStatus.ACCEPTED
                submission.save()
            elif action.action_type == SubmissionActionType.REJECT:
                submission.status = SubmissionStatus.REJECTED
                submission.save()
    @classmethod
    def validate_submission_action_payload(cls, submission, action_type, payload, context, **kwargs):
        if submission.current_stage == 0 and action_type == SubmissionActionType.SEND_TO_DETECTIVE:
            if "case_id" not in payload:
                raise ValidationError({"payload": {"case_id": "This field is required."}})
            try:
                case_id = int(payload["case_id"])
                case = Case.objects.get(id=case_id)
            except (ValueError, Case.DoesNotExist):
                raise ValidationError({"payload": {"case_id": "Invalid case ID."}})
            if not case.lead_detective:
                raise ValidationError({"payload": {"case_id": "The specified case does not have a lead detective assigned."}})
        
        if submission.current_stage == 1 and action_type == SubmissionActionType.SET_REWARD:
            if "reward_amount" not in payload:
                raise ValidationError({"payload": {"reward_amount": "This field is required."}})
            try:
                reward_amount = int(payload["reward_amount"])
                if reward_amount <= 0:
                    raise ValidationError({"payload": {"reward_amount": "Reward amount must be a positive integer."}})
            except ValueError:
                raise ValidationError({"payload": {"reward_amount": "Reward amount must be an integer."}})
        
    @classmethod
    def can_submit(cls, user: User, obj):
        return True