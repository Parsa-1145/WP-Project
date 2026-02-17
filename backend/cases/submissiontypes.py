from submissions.submissiontypes.classes import BaseSubmissionType
from cases.models import Complaint, CrimeScene
from cases.serializers import ComplaintSerializer, CrimeSceneSerializer
from submissions.models import SubmissionStage

class ComplaintSubmissionType(BaseSubmissionType["Complaint"]):
    type_key = "COMPLAINT"
    display_name = "Complaint"
    serializer_class = ComplaintSerializer
    create_group = []
    model_class=Complaint

    @classmethod
    def handle_submission_event(cls, submission_obj, event, **kwargs):
        return super().handle_submission_event(submission_obj, event, **kwargs)
    
    @classmethod
    def on_submit(cls, submission):
        stage_1 = SubmissionStage.objects.create(
            submission=submission,
            target_permissions="CADET",
            order=0
        )
        stage_2 = SubmissionStage.objects.create(
            submission=submission,
            target_permissions="OFFICER",
            order=1
        )
    
class CrimeSceneSubmissionType(BaseSubmissionType["CrimeScene"]):
    type_key = "CRIME_SCENE"
    display_name = "Crime Scene"
    serializer_class = CrimeSceneSerializer
    create_group = []
    model_class=CrimeScene

    @classmethod
    def handle_submission_event(cls, submission_obj, event, **kwargs):
        return super().handle_submission_event(submission_obj, event, **kwargs)