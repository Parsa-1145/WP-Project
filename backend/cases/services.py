from .models import Case, CrimeScene, Complaint, CaseSubmissionLink
from django.db import transaction
from rest_framework.serializers import ValidationError

@transaction.atomic
def create_case_from_complaint(complaint: Complaint) -> Case:
    case = Case.objects.create(
        title=complaint.title,
        description=complaint.description,
        crime_datetime=complaint.crime_datetime
    )
    case.complainants.set(complaint.complainants.all())
    
    return case

@transaction.atomic
def create_case_from_crime_scene(crime_scene: CrimeScene) -> Case:
    case = Case.objects.create(
        title=crime_scene.title,
        description=crime_scene.description,
        witnesses=crime_scene.witnesses or [],
        crime_datetime=crime_scene.crime_datetime
    )
    return case

@transaction.atomic
def attach_submission_to_case(*, submission, case, relation_type="ORIGIN") -> CaseSubmissionLink:
    link, created = CaseSubmissionLink.objects.get_or_create(
        submission=submission,
        defaults={"case": case, "relation_type": relation_type},
    )
    if not created and link.case_id != case.id:
        raise ValidationError("This submission is already linked to a different case.")
    return link