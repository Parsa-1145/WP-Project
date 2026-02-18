from .models import Case, CrimeScene, Complaint
from django.db import transaction

@transaction.atomic
def create_case_from_complaint(complaint: Complaint):
    pass

@transaction.atomic
def create_case_from_crime_scene(crime_scene: CrimeScene):
    pass
