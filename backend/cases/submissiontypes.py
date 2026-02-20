from submissions.submissiontypes.classes import BaseSubmissionType
from cases.models import Complaint, CrimeScene, CaseSubmissionLink
from cases.serializers import (
    ComplaintSerializer,
    ComplaintPayloadSerializer,
    CrimeSceneSerializer,
    CaseStaffingSubmissionPayloadSerializer,
    InvestigationResultsApprovalPayloadSerializer,
    InvestigationResultsApprovalTargetSerializer,
)
from submissions.models import SubmissionStage, SubmissionActionType, Submission, SubmissionAction, SubmissionStatus
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import serializers
from cases.models import Case
from drf_spectacular.utils import OpenApiExample, inline_serializer
from accounts.models import User

class ComplaintSubmissionType(BaseSubmissionType["Complaint"]):
    type_key             = "COMPLAINT"
    display_name         = "Complaint"
    serializer_class     = ComplaintSerializer
    create_permissions   = []
    model_class          = Complaint
    api_request_schema   = ComplaintPayloadSerializer
    api_request_payload_example  = {
        "title":"title",
        "description":"description",
        "crime_datetime": "2026-02-17T21:35:00Z",
        "complainant_national_ids":[
            "2581801910",
            "  2591892340"
        ]
    }
    api_response_target_example = {
        "id": 1,
        "title": "KMKH",
        "description": "KMKH",
        "crime_datetime": "2026-02-18T01:05:00+03:30",
        "complainant_national_ids": ["1111111111", "2222222222"],
    }

    @classmethod
    def handle_submission_action(cls, submission: Submission, action: SubmissionAction, context, **kwargs):
        from .services import attach_submission_to_case, create_case_from_complaint
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
            
            ser = ComplaintPayloadSerializer(
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
    def validate_submission_data(cls, data, context):
        serializer = ComplaintPayloadSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        return serializer
    
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
    model_class         = CrimeScene
    api_request_payload_example = {
            "title" : "KMKH",
            "description" : "KMKH",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "witnesses" : [{"phone_number": "989112405786", "national_id": "2222222222"}, {"phone_number": "989112405786", "national_id": "   3333333333   "}]
        }
    api_response_target_example =  {
        "id": 1,
        "title": "Crime Scene A",
        "description": "desc",
        "witnesses": [
        {
            "phone_number": "+989112405786",
            "national_id": "2222222222"
        },
        {
            "phone_number": "+989112405787",
            "national_id": "3333333333"
        }
        ],
        "crime_datetime": "2026-02-18T01:05:00+03:30"
    }
    api_request_schema = CrimeSceneSerializer

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
        from .services import attach_submission_to_case, create_case_from_crime_scene

        case = create_case_from_crime_scene(crime_scene=crime_scene)
        attach_submission_to_case(
            case=case,
            submission=submission,
            relation_type=CaseSubmissionLink.RelationType.ORIGIN
        )

class CaseStaffingSubmissionType(BaseSubmissionType["Case"]):
    type_key             = "CASE_STAFFING"
    display_name         = "Case Staffing"
    create_permissions   = ["case.add_case_acceptance_submission"]
    model_class          = Case
    serializer_class     = CaseStaffingSubmissionPayloadSerializer
    can_be_created_from_request = False
    api_request_payload_example = None
    api_response_target_example = {
      "id": 1,
      "title": "Test Title",
      "description": "test description",
      "crime_datetime": "2026-02-18T01:05:00+03:30",
      "crime_level": "L3",
      "lead_detective": "Not Assigned",
      "supervisor": "Not Assigned",
      "origin_submission_id": 1
    }
    api_request_schema           = None

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
        stage = SubmissionStage.objects.filter(submission=submission, order=submission.current_stage).first()

        target = cls.get_object(submission.object_id)

        if stage.order == 0:
            if action.action_type == SubmissionActionType.ACCEPT:
                if target.complainants.contains(context["request"].user):
                    raise PermissionDenied("A complainant of the case cannot be the lead detective")
                target.lead_detective = context["request"].user
                target.status = target.Status.AWAITING_SUPERVISOR_ACCEPTANCE
                target.save()

                submission.current_stage = 1
                submission.save()
        if stage.order == 1:
            if action.action_type == SubmissionActionType.ACCEPT:
                if target.lead_detective == context["request"].user:
                    raise PermissionDenied("Lead detective cannot approve as supervisor.")
                if target.complainants.contains(context["request"].user):
                    raise PermissionDenied("A complainant of the case cannot be the supervisor")
                target.supervisor = context["request"].user
                target.status = Case.Status.OPEN_INVESTIGATION
                target.save()


                submission.status = SubmissionStatus.ACCEPTED
                submission.save()

class InvestigationResultsApprovalSubmissionType(BaseSubmissionType["Case"]):
    type_key             = "INVESTIGATION_APPROVAL"
    display_name         = "Investigation Approval"
    create_permissions   = ["case.investigate_on_case"]
    model_class          = Case
    serializer_class     = InvestigationResultsApprovalTargetSerializer
    api_request_payload_example = {
        "case_id": 1
    }
    api_response_target_example = {
      "id": 1,
      "title": "Test Title",
      "description": "test description",
      "crime_datetime": "2026-02-18T01:05:00+03:30",
      "crime_level": "L3",
      "suspects" : [
          {
              "name" : "parsa zamiri",
              "national_id" : "1234567890",
              "criminal_record" : [
                  {
              "case_id" : 1,
              "title"   : "Case",
              "description" : "description",
              "crime_datetime" : "2026-02-18T01:05:00+03:30",
              "status"         : "closed"
                  }
              ]
          }
      ]
    }
    api_request_schema           = InvestigationResultsApprovalPayloadSerializer

    @classmethod
    def validate_submission_data(cls, data, context):
        case_id = data.get("case_id")
        if case_id is None:
            raise ValidationError({"case_id":"this field is required"})
        
        case = Case.objects.get(pk=case_id)

        if case is None:
            raise ValidationError({"case_id":"case doesnt exist"})
        
        user:User = context["request"].user

        if case.lead_detective != user:
            raise PermissionDenied("only the lead detective can make this request")
            
    @classmethod
    def create_object(cls, payload, context):
        case_id = payload.get("case_id")
        
        return Case.objects.get(pk=case_id)
