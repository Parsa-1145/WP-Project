from accounts.models import User
from rest_framework.test import APITestCase
from submissions.models import (
    Submission,
    SubmissionAction,
    SubmissionStage,
    SubmissionActionType,
    SubmissionStatus,
)
from .models import BailRequest, Reward
from .submissiontypes import BailRequestSubmissionType
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.utils import timezone
import json
import uuid


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


class RewardModelTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="reward_user",
            password="testpass",
            status=User.Status.FREE,
        )

        cls.submission = Submission.objects.create(
            submission_type="test_reward_submission",
            created_by=cls.user,
            # Minimal required fields; object_id is arbitrary here
            object_id=1,
            # stages are zero-indexed; use the initial stage (0)
            current_stage=0,
            status=SubmissionStatus.ACCEPTED,
        )

    def test_reward_defaults_and_str(self):
        reward = Reward.objects.create(
            user=self.user,
            submission=self.submission,
            amount=1000000,
        )

        assert reward.status == Reward.Status.PENDING
        assert reward.claimed_at is None
        assert isinstance(reward.unique_code, uuid.UUID)
        assert reward.user == self.user
        assert reward.submission == self.submission

        # __str__ should include the unique code and username
        s = str(reward)
        assert "Reward" in s
        assert self.user.username in s

    def test_reward_claim_sets_status_and_claimed_at(self):
        reward = Reward.objects.create(
            user=self.user,
            submission=self.submission,
            amount=500000,
        )

        reward.claim()
        reward.refresh_from_db()

        assert reward.status == Reward.Status.CLAIMED
        assert reward.claimed_at is not None

    def test_reward_cannot_be_claimed_twice(self):
        reward = Reward.objects.create(
            user=self.user,
            submission=self.submission,
            amount=750000,
        )

        reward.claim()
        first_claimed_at = reward.claimed_at

        try:
            reward.claim()
            assert False, "Second claim should raise ValueError"
        except ValueError:
            pass

        reward.refresh_from_db()
        assert reward.status == Reward.Status.CLAIMED
        assert reward.claimed_at == first_claimed_at

    def test_reward_creation_without_submission(self):
        """
        Reward should be creatable without linking to a submission.
        """
        reward = Reward.objects.create(
            user=self.user,
            amount=2_000_000,
        )

        assert reward.pk is not None
        assert reward.user == self.user
        assert reward.submission is None
        assert reward.status == Reward.Status.PENDING
        assert reward.claimed_at is None


class RewardCreationOnEvidenceApprovalTestCase(APITestCase):
    """
    When evidence (e.g. bio evidence) is submitted and then approved,
    a Reward should be created for the submitter, linked to that submission.
    """

    @classmethod
    def add_perms(cls, user: User, *codenames):
        for perm in codenames:
            if "." in perm:
                app_label, codename = perm.split(".", 1)
                p = Permission.objects.get(
                    content_type__app_label=app_label, codename=codename
                )
            else:
                p = Permission.objects.get(codename=perm)
            user.user_permissions.add(p)

    @classmethod
    def setUpTestData(cls):
        from cases.models import Case
        from evidence.models import BioEvidence
        from evidence.submissiontypes import BioEvidenceSubmissionType

        cls.citizen = User.objects.create_user(
            username="evidence_citizen",
            password="testpass",
            status=User.Status.FREE,
        )
        cls.approver = User.objects.create_user(
            username="evidence_approver",
            password="testpass",
            status=User.Status.FREE,
        )
        cls.add_perms(cls.approver, "evidence.can_approve_bioevidence")

        cls.case = Case.objects.create(
            title="Reward test case",
            description="Case for reward creation test",
            crime_datetime=timezone.now(),
        )
        cls.bio_evidence = BioEvidence.objects.create(
            case=cls.case,
            recorder=cls.approver,
            title="Bio evidence",
            description="Sample bio evidence",
        )
        cls.submission = Submission.objects.create(
            submission_type=BioEvidenceSubmissionType.type_key,
            object_id=cls.bio_evidence.pk,
            created_by=cls.citizen,
            status=SubmissionStatus.PENDING,
            current_stage=0,
        )
        SubmissionStage.objects.create(
            submission=cls.submission,
            target_permission="evidence.can_approve_bioevidence",
            order=0,
            allowed_actions=[
                SubmissionActionType.ACCEPT,
                SubmissionActionType.REJECT,
            ],
        )

    def test_reward_created_when_evidence_approved(self):
        """Approving an evidence submission creates a Reward for the submitter."""
        from evidence.submissiontypes import BioEvidenceSubmissionType

        reward_amount = 500_000
        action = SubmissionAction.objects.create(
            submission=self.submission,
            action_type=SubmissionActionType.ACCEPT,
            payload={"reward_amount": reward_amount, "coroner_result": "Verified."},
            created_by=self.approver,
        )

        BioEvidenceSubmissionType.handle_submission_action(
            self.submission, action, context=None
        )

        self.submission.refresh_from_db()
        assert self.submission.status == SubmissionStatus.ACCEPTED

        rewards = list(Reward.objects.filter(submission=self.submission))
        assert len(rewards) == 1
        reward = rewards[0]
        assert reward.user == self.citizen
        assert reward.submission == self.submission
        assert reward.amount == reward_amount
        assert reward.status == Reward.Status.PENDING
        assert reward.claimed_at is None
        assert reward.unique_code is not None