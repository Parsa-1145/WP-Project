from accounts.models import User
from submissions.models import Submission, SubmissionAction
from submissions.submissiontypes.classes import BaseSubmissionType
from .models import BioEvidence
from .serializers import BioEvidenceSerializer
from submissions.models import SubmissionStage, SubmissionActionType, SubmissionStatus

class BioEvidenceSubmissionType(BaseSubmissionType["BioEvidence"]):
    type_key = "BIO_EVIDENCE"
    display_name = "Bio Evidence Approval"
    serializer_class = BioEvidenceSerializer
    create_permissions = []
    model_class = BioEvidence
    api_request_schema = BioEvidenceSerializer
    can_be_created_from_request = False
    api_request_payload_example = { # TODO: complete example
        "TODO":""
    }
    api_response_target_example = {
        "TODO":""
    }


    @classmethod
    def on_submit(cls, submission: Submission) -> None:
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="evidence.can_approve_bioevidence",
            order=0,
            allowed_actions=[SubmissionActionType.ACCEPT, SubmissionActionType.REJECT],
            prompt="Review this bio evidence and either verify (accept) or reject it."
        )
        submission.current_stage = 0

    @classmethod
    def handle_submission_action(cls, submission: Submission, action: SubmissionAction, context, **kwargs):
        evi = cls.get_object(submission.object_id)
        if action.action_type == SubmissionActionType.ACCEPT :
            # serializer = BioEvidenceSerializer(
            #     instance=cls.get_object(submission.object_id),
            #     context=context or {},
            #     data=action.payload or {},
            #     partial=True
            # )
            # serializer.is_valid(raise_exception=True)
            # serializer.save(is_approved=True, )

            evi.is_verified = True
            evi.save()


            result_text = action.payload.get("coroner_result")
            submission.status = SubmissionStatus.ACCEPTED
            submission.save()

        elif action.action_type == SubmissionActionType.REJECT :
            # serializer = BioEvidenceSerializer(
            #     instance=cls.get_object(submission.object_id),
            #     context=context or {},
            #     data=action.payload or {},
            #     partial=True
            # )

            evi.is_verified = False
            evi.save()


            submission.status = SubmissionStatus.REJECTED
            submission.save()
    @classmethod
    def can_user_submit(cls, user: User) -> bool:
        return False
