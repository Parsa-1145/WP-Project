from accounts.models import User
from rest_framework.test import APITestCase
from submissions.models import (
    Submission,
    SubmissionAction,
    SubmissionStage,
    SubmissionActionType,
    SubmissionStatus,
)
from .models import BailRequest
from .submissiontypes import BailRequestSubmissionType
from django.urls import reverse
from django.contrib.auth.models import Permission
import json


class BailRequestTestCase(APITestCase):
    def printJ(self, data):
        print(json.dumps(data.json(), indent=2))
    
    @classmethod
    def add_perms(cls, user: User, *codenames):
        for codename in codenames:
            user.user_permissions.add(Permission.objects.get(codename=codename))
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            status=User.Status.ARRESTED,
        )

        cls.approver = User.objects.create_user(
            username="approver",
            password="approverpass",
            status=User.Status.FREE,
        )
        cls.add_perms(cls.approver, "can_approve_bail_request")

        cls.submission_create_url = reverse("submission-create")
        cls.submission_action_url = lambda submission_id: reverse("submission-action-list-create", args=[submission_id])


    def create_submission(self, user: User):
        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.submission_create_url,
            format="json",
            data={
                "submission_type": BailRequestSubmissionType.type_key,
                "payload": {}
            },
        )
        assert response.status_code == 201
        return Submission.objects.get(id=response.data["id"])



    def test_bail_request_creation(self):
        submission = self.create_submission(self.user)
        assert submission.submission_type == BailRequestSubmissionType.type_key
        assert submission.created_by == self.user
        bail_request = BailRequest.objects.get(id=submission.object_id)
        assert bail_request.requested_by == self.user
        assert bail_request.status == BailRequest.Status.PENDING

    def test_bail_request_approval(self):
        submission = self.create_submission(self.user)
        bail = BailRequest.objects.get(id=submission.object_id)

        self.client.force_authenticate(user=self.approver)
        response = self.client.post(
            self.submission_action_url(submission.id),
            format="json",
            data={
                "action_type": SubmissionActionType.ACCEPT,
                "payload": {"amount": 500000},
            }
        )
        self.printJ(response)
        assert response.status_code == 201, response.data

        bail.refresh_from_db()
        submission.refresh_from_db()

        assert bail.status == BailRequest.Status.APPROVED
        assert bail.amount == 500000
        assert submission.status == SubmissionStatus.ACCEPTED

    def test_bail_request_rejection(self):
        submission = self.create_submission(self.user)
        bail = BailRequest.objects.get(id=submission.object_id)
        
        self.client.force_authenticate(user=self.approver)
        response = self.client.post(
            self.submission_action_url(submission.id),
            format="json",
            data={
                "action_type": SubmissionActionType.REJECT,
                "payload": {"message": "Insufficient information"},
            }
        )
        assert response.status_code == 201, response.data

        bail.refresh_from_db()
        submission.refresh_from_db()

        assert bail.status == BailRequest.Status.REJECTED
        assert submission.status == SubmissionStatus.REJECTED

    def test_can_submit_allows_arrested_without_pending_bail(self):
        can_submit = BailRequestSubmissionType.can_submit(self.user, obj=None)
        assert can_submit is True

    def test_can_submit_blocks_when_pending_bail_exists(self):
        BailRequest.objects.create(
            amount=100,
            requested_by=self.user,
            status=BailRequest.Status.PENDING,
        )

        can_submit = BailRequestSubmissionType.can_submit(self.user, obj=None)
        assert can_submit is False

    def test_can_submit_denies_non_arrested_user(self):
        
        can_submit = BailRequestSubmissionType.can_submit(self.approver, obj=None)
        assert can_submit is False