from submissions.submissiontypes.classes import BaseSubmissionType
from cases.models import Complaint, CrimeScene
from cases.serializers import ComplaintSerializer, CrimeSceneSerializer
from submissions.models import SubmissionStage, SubmissionActionType, Submission, SubmissionAction, SubmissionStatus
from rest_framework.serializers import ValidationError
from cases.models import Case

class ComplaintSubmissionType(BaseSubmissionType["Complaint"]):
    type_key = "COMPLAINT"
    display_name = "Complaint"
    serializer_class = ComplaintSerializer
    create_permissions = []
    model_class=Complaint

    @classmethod
    def handle_submission_action(cls, submission: Submission, action: SubmissionAction, context, **kwargs):
        context = context or {}
        stage = SubmissionStage.objects.filter(
            submission=submission,
            order=submission.current_stage
        ).first()
        if stage is None:
            raise ValidationError("Submission stage corrupted")
        
        target = cls.get_object(submission.object_id)

        if stage.order == 0:
            if action.action_type != SubmissionActionType.RESUBMIT:
                return
            
            ser = ComplaintSerializer(
                instance=target,
                data=action.payload or {},
                partial=True,
                context=context,
            )
            ser.is_valid(raise_exception=True)
            ser.save()

            submission.current_stage = 1
            submission.save()
        elif stage.order == 1:
            stage.target_user = action.created_by
            stage.target_permission = None
            stage.save()
            if action.action_type == SubmissionActionType.REJECT:
                if SubmissionAction.objects.filter(submission=submission, action_type=SubmissionActionType.REJECT).count() >= 4:
                    submission.status=SubmissionStatus.REJECTED
                    return
                submission.current_stage = 0
                submission.save()
            if action.action_type == SubmissionActionType.APPROVE:
                submission.current_stage = 2
                submission.save()
        elif stage.order == 2:
            if action.action_type == SubmissionActionType.REJECT:
                submission.current_stage = 1
                submission.save()
            if action.action_type == SubmissionActionType.APPROVE:
                submission.status=SubmissionStatus.APPROVED
                
                print("case created todo") #TODO
    
    @classmethod
    def on_submit(cls, submission):
        SubmissionStage.objects.create(
            submission=submission,
            target_user=submission.created_by,
            order=0,
            allowed_actions=[SubmissionActionType.RESUBMIT]
        )
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="cases.first_complaint_review",
            order=1,
            allowed_actions=[SubmissionActionType.REJECT, SubmissionActionType.APPROVE]
        )
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="cases.final_complaint_review",
            order=2,
            allowed_actions=[SubmissionActionType.REJECT, SubmissionActionType.APPROVE]
        )

        submission.current_stage = 1
        submission.save()
    
class CrimeSceneSubmissionType(BaseSubmissionType["CrimeScene"]):
    type_key = "CRIME_SCENE"
    display_name = "Crime Scene"
    serializer_class = CrimeSceneSerializer
    create_permissions = ["cases.create_crime_scene"]
    model_class=CrimeScene