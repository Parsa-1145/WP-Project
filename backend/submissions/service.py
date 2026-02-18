from django.db import transaction
from django.db.models import Model
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from .models import *
from core import settings
from .submissiontypes.registry import get_submission_type
from .submissiontypes.classes import BaseSubmissionType
    
@transaction.atomic
def create_submission(
    *,
    submission_type_cls: type[BaseSubmissionType],
    target: Model,
    created_by: AbstractUser = None
    ) -> Submission:
    
    submission = Submission.objects.create(
        submission_type=submission_type_cls.type_key,
        object_id=target.pk,
        status=SubmissionStatus.PENDING,
        created_by=created_by
    )

    submission_type_cls.on_submit(submission=submission)

    if created_by is not None:
        submit_action = SubmissionAction.objects.create(
            submission = submission,
            action_type = SubmissionActionType.SUBMIT,
            created_by = created_by,
            payload={}
        )

    return submission