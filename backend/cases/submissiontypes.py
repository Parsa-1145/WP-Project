from submissions.submissiontypes.classes import BaseSubmissionType
from cases.models import Complaint, CrimeScene, CaseSubmissionLink
from cases.serializers import ComplaintSerializer, CrimeSceneSerializer
from submissions.models import SubmissionStage, SubmissionActionType, Submission, SubmissionAction, SubmissionStatus
from rest_framework.exceptions import ValidationError, PermissionDenied
from cases.models import Case
from drf_spectacular.utils import OpenApiExample


class ComplaintSubmissionType(BaseSubmissionType["Complaint"]):
    type_key             = "COMPLAINT"
    display_name         = "Complaint"
    serializer_class     = ComplaintSerializer
    create_permissions   = []
    model_class          = Complaint
    api_schema           = ComplaintSerializer()
    api_payload_example  = {
        "title":"title",
        "description":"description",
        "crime_datetime": "2026-02-17T21:35:00Z",
        "complainants":[
            "2581801910",
            "  2591892340"
        ]
    }

    @classmethod
    def handle_submission_action(cls, submission: Submission, action: SubmissionAction, context, **kwargs):
        from .services import attach_submission_to_case, create_case_from_crime_scene, create_case_from_complaint
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
                if SubmissionAction.objects.filter(submission=submission, action_type=SubmissionActionType.RESUBMIT).count() >= 3:
                    submission.status=SubmissionStatus.REJECTED
                    submission.save()
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
                submission.save()

                case = create_case_from_complaint(complaint=target)
                attach_submission_to_case(
                    case=case,
                    submission=submission,
                    relation_type=CaseSubmissionLink.RelationType.ORIGIN
                )
    
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
            target_permission="cases.complaint_initial_approve",
            order=1,
            allowed_actions=[SubmissionActionType.REJECT, SubmissionActionType.APPROVE]
        )
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="cases.complaint_final_approve",
            order=2,
            allowed_actions=[SubmissionActionType.REJECT, SubmissionActionType.APPROVE]
        )

        submission.current_stage = 1
        submission.save()
    
class CrimeSceneSubmissionType(BaseSubmissionType["CrimeScene"]):
    type_key            = "CRIME_SCENE"
    display_name        = "Crime Scene"
    serializer_class    = CrimeSceneSerializer
    create_permissions  = ["cases.add_crimescene"]
    model_class         =CrimeScene
    api_payload_example ={
            "title" : "KMKH",
            "description" : "KMKH",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "witnesses" : [{"phone_number": "989112405786", "national_id": "2222222222"}, {"phone_number": "989112405786", "national_id": "   3333333333   "}]
        }
    api_schema = CrimeSceneSerializer()

    @classmethod
    def on_submit(cls, submission: Submission):
        target = cls.get_object(submission.object_id)

        if submission.created_by.has_perm("cases.approve_crime_scene"):
            submit_action = SubmissionAction.objects.create(
                submission = submission,
                action_type = SubmissionActionType.APPROVE,
                created_by = submission.created_by,
                payload={}
            )

            submission.status = SubmissionStatus.APPROVED
            
            cls.create_case(submission, target)

            submission.save()
            return
        
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="cases.approve_crime_scene",
            order=0,
            allowed_actions=[SubmissionActionType.APPROVE, SubmissionActionType.REJECT]
        )

    @classmethod
    def handle_submission_action(cls, submission:Submission, action:SubmissionAction, context, **kwargs):
        target = cls.get_object(submission.object_id)
        if submission.current_stage == 0:
            if action.action_type == SubmissionActionType.APPROVE:
                submission.status = SubmissionStatus.APPROVED
                cls.create_case(
                    submission,
                      target)
            if action.action_type == SubmissionActionType.REJECT:
                submission.status = SubmissionStatus.REJECTED

        submission.save()

    @classmethod
    def create_case(cls, submission: Submission, crime_scene: CrimeScene):
        from .services import attach_submission_to_case, create_case_from_crime_scene, create_case_from_complaint
        case = create_case_from_crime_scene(crime_scene=crime_scene)
        attach_submission_to_case(
            case=case,
            submission=submission,
            relation_type=CaseSubmissionLink.RelationType.ORIGIN
        )

class CaseAcceptanceSubmissionType(BaseSubmissionType["Case"]):
    type_key             = "CASE_ACCEPTANCE"
    display_name         = "Case Acceptance"
    create_permissions   = []
    model_class          =Complaint
    serializer_class     = None
    api_payload_example  = None
    api_schema           = None

    @classmethod
    def on_submit(cls, submission):
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="cases.investigate_on_case",
            order=0,
            allowed_actions=[SubmissionActionType.ACCEPT]
        )
        SubmissionStage.objects.create(
            submission=submission,
            target_permission="cases.supervise_case",
            order=1,
            allowed_actions=[SubmissionActionType.ACCEPT]
        )
        return super().on_submit(submission)

    @classmethod
    def handle_submission_action(cls, submission, action, context, **kwargs):
        from .services import attach_submission_to_case, create_case_from_crime_scene, create_case_from_complaint
        stage = SubmissionStage.objects.filter(submission=submission, order=submission.current_stage).first()

        target = cls.get_object(submission.object_id)

        if stage.order == 0:
            if action.action_type == SubmissionActionType.ACCEPT:
                target.lead_detective = context["request"].user
                target.status = target.Status.AWAITING_SUPERVISOR_ACCEPTANCE

                submission.current_stage = 1
                submission.save()
        if stage.order == 1:
            if action.action_type == SubmissionActionType.ACCEPT:
                if target.lead_detective == context["request"].user:
                    raise PermissionDenied("Lead detective cannot approve as supervisor.")
                target.supervisor = context["request"].user
                target.status = Case.Status.OPEN_INVESTIGATION

                submission.status = SubmissionStatus.ACCEPTED
                submission.save()