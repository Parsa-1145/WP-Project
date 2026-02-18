from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from accounts.models import User
from accounts.serializers.fields import NationalIDField
from django.contrib.auth.models import Permission
from django.http import HttpResponse
import json
from submissions.models import SubmissionActionType
from .models import Case
#TODO actual test
# TODO: actual assertions (currently this is an interactive workflow trace)
class AuthFlowTests(APITestCase):

    def add_perms(self, user:User, *codenames):
        for c in codenames:
            print(c)
            user.user_permissions.add(Permission.objects.get(codename=c))

    def setUp(self):
        # Users:
        # u1 = creator / submitter (no review perms)
        # u2 = first reviewer (first_complaint_review)
        # u3 = final reviewer + can create crime scenes (final_complaint_review, create_crime_scene)
        # u4 = first reviewer + can create crime scenes (first_complaint_review, create_crime_scene)
        self.u1 = User.objects.create_user(
            username="creator",
            password="pass12345",
            national_id="1111111111",
            phone_number="+989121234567",
        )
        self.u2 = User.objects.create_user(
            username="u1",
            password="pass12345",
            national_id="2222222222",
            phone_number="+989121234568",
        )
        self.u3 = User.objects.create_user(
            username="u3",
            password="pass12345",
            national_id="3333333333",
            phone_number="+989121234569",
        )
        self.u4 = User.objects.create_user(
            username="u4",
            password="pass12345",
            national_id="3333333333",
            phone_number="+989121234569",
        )

        self.add_perms(self.u2, "first_complaint_review")
        self.add_perms(self.u3, "final_complaint_review", "create_crime_scene")
        self.add_perms(self.u4, "first_complaint_review", "create_crime_scene")

        # Endpoints
        self.submission_type_list_url            = reverse("submission-type-list")
        self.submission_inbox_list_url           = reverse("submission-inbox-list")
        self.submission_mine_list_create_url     = reverse("submission-mine-list-create")

    # Helpers
    def send_submission(self, submission_type, payload) -> HttpResponse:
        # Create a new submission (mine)
        return self.client.post(
            self.submission_mine_list_create_url,
            data={"submission_type": submission_type, "payload": payload},
            format="json",
        )

    def send_submission_action(self, action_type: SubmissionActionType, payload, submission_id) -> HttpResponse:
        # Append an action to an existing submission (approve/reject/resubmit/etc.)
        url = reverse("submission-action-list-create", kwargs={"pk": submission_id})
        return self.client.post(url, data={"action_type": action_type, "payload": payload}, format="json")

    def get_submissions_inbox(self):
        # Inbox: submissions currently assigned/visible to this user to act on
        return self.client.get(self.submission_inbox_list_url, format="json")

    def get_submission_action_types(self, submission_id):
        # Returns allowed actions for the *current stage* of the submission for this user
        url = reverse("submission-action-type", kwargs={"pk": submission_id})
        return self.client.get(url, format="json")

    def get_my_submissions(self):
        # Submissions created by authenticated user
        return self.client.get(self.submission_mine_list_create_url, format="json")

    def get_submission_action_history(self, submission_id):
        # Full action history list endpoint
        url = reverse("submission-action-list-create", kwargs={"pk": submission_id})
        return self.client.get(url, format="json")

    def printJ(self, response: HttpResponse):
        print(json.dumps(response.json(), indent=3))

    def test_complaint_creation(self):
        # ---------------------------------------------------------------------
        # 0) Capability discovery: each user asks "what submission types can I create?"
        # ---------------------------------------------------------------------
        self.client.force_authenticate(self.u1)
        res = self.client.get(self.submission_type_list_url)
        print(res.json())

        self.client.force_authenticate(self.u2)
        res = self.client.get(self.submission_type_list_url)
        print(res.json())

        self.client.force_authenticate(self.u3)
        res = self.client.get(self.submission_type_list_url)
        print(res.json())

        # ---------------------------------------------------------------------
        # 1) u1 creates COMPLAINT submissions with varying payload validity.
        #    This block is effectively testing payload validation/normalization:
        #    - duplicates in complainant IDs
        #    - trimming whitespace
        #    - unknown/invalid IDs
        #    - invalid format ("555555 5")
        # ---------------------------------------------------------------------
        self.client.force_authenticate(self.u1)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   2222222222  "],
            },
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   3333333333  "],
            },
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   4444444444  "],
            },
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   4444444444  ", "  555555 5"],
            },
        )
        self.printJ(res)

        # ---------------------------------------------------------------------
        # 2) Inbox visibility check:
        #    same inbox endpoint, different authenticated users.
        #    This reveals which stage/assignment logic routes complaints to reviewers.
        # ---------------------------------------------------------------------
        self.printJ(self.get_submissions_inbox())

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submissions_inbox())

        self.client.force_authenticate(self.u3)
        self.printJ(self.get_submissions_inbox())

        # ---------------------------------------------------------------------
        # 3) Crime scene submission creation tests:
        #    u3 can create crime scene submissions (has create_crime_scene).
        #    Test witness nested payload validation (IDs + phone numbers + trimming).
        # ---------------------------------------------------------------------
        self.client.force_authenticate(self.u3)
        res = self.send_submission(
            submission_type="CRIME_SCENE",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "witnesses": [
                    {"phone_number": "989112405786", "national_id": "   2222222222   "},
                    {"phone_number": "989112405786", "national_id": "   3333333333   "},
                ],
            },
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="CRIME_SCENE",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "witnesses": [
                    {"phone_number": "989112405786", "national_id": "2222222222"},
                    {"phone_number": "989112405786", "national_id": "2222232222"},
                ],
            },
        )
        self.printJ(res)

        # u2 attempts to create CRIME_SCENE without create_crime_scene perm => expect 403/denied
        self.client.force_authenticate(self.u2)
        res = self.send_submission(
            submission_type="CRIME_SCENE",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "witnesses": [
                    {"phone_number": "989112405786", "national_id": "2222222222"},
                    {"phone_number": "989112405786", "national_id": "2222232222"},
                ],
            },
        )
        self.printJ(res)

        # ---------------------------------------------------------------------
        # 4) "My submissions" visibility:
        #    each user checks their own list endpoint.
        # ---------------------------------------------------------------------
        self.client.force_authenticate(self.u1)
        self.printJ(self.get_my_submissions())

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_my_submissions())

        self.client.force_authenticate(self.u3)
        self.printJ(self.get_my_submissions())

        # ---------------------------------------------------------------------
        # 5) Action attempts on submission id=1:
        #    This section explores permissions/allowed actions by stage.
        #    Multiple users attempt RESUBMIT/REJECT/APPROVE and observe results.
        # ---------------------------------------------------------------------

        # Unclear auth context here (currently u3). Attempt resubmit on submission 1
        self.printJ(self.send_submission_action(SubmissionActionType.RESUBMIT, {}, 1))

        # u1 tries to resubmit their submission (often allowed only after reject)
        self.client.force_authenticate(self.u1)
        self.printJ(self.send_submission_action(SubmissionActionType.RESUBMIT, {}, 1))

        # u2 (first reviewer) tries resubmit and reject/approve actions (stage-gated)
        self.client.force_authenticate(self.u2)
        self.printJ(self.send_submission_action(SubmissionActionType.RESUBMIT, {}, 1))
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {}, 1))

        self.printJ(self.send_submission_action(SubmissionActionType.APPROVE, {}, 1))
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(SubmissionActionType.APPROVE, {}, 1))

        # u1 checks their submissions after reviewer actions
        self.client.force_authenticate(self.u1)
        self.printJ(self.get_my_submissions())

        # ---------------------------------------------------------------------
        # 6) Final reviewer stage interactions (u3):
        #    u3 checks inbox, tries invalid SUBMIT as an action, rejects with message, re-checks inbox.
        # ---------------------------------------------------------------------
        self.client.force_authenticate(self.u3)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(SubmissionActionType.SUBMIT, {}, 1))
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {"message": "boba loves trump"}, 1))
        self.printJ(self.get_submissions_inbox())

        # ---------------------------------------------------------------------
        # 7) Cross-user inbox checks after state transitions:
        #    u4/u2/u1 observe what changed.
        # ---------------------------------------------------------------------
        self.client.force_authenticate(self.u4)
        self.printJ(self.get_submissions_inbox())

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {"message": "kmkh"}, 1))
        self.printJ(self.get_submissions_inbox())

        self.client.force_authenticate(self.u1)
        self.printJ(self.get_submissions_inbox())

        # ---------------------------------------------------------------------
        # 8) Resubmission payload tests:
        #    u1 resubmits with various payloads to test:
        #    - invalid IDs
        #    - switching complainants
        #    - duplicate IDs normalization/validation
        # ---------------------------------------------------------------------
        self.printJ(self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   4444444444  ", "  555555 5"],
            },
            1,
        ))

        self.printJ(self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH2",
                "description": "KMKH2",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["3333333333", "   2222222222  "],
            },
            1,
        ))

        self.printJ(self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH",
                "description": "KMKH",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   2222222222  "],
            },
            1,
        ))

        # ---------------------------------------------------------------------
        # 9) Reviewer rejects again; submitter resubmits again; repeated cycles.
        #    This is exercising the stage machine transitions and allowed_actions.
        # ---------------------------------------------------------------------
        self.printJ(self.get_submissions_inbox())

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {"message": "kmkh"}, 1))
        self.printJ(self.get_submissions_inbox())

        self.client.force_authenticate(self.u1)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH3",
                "description": "KMKH3",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   2222222222  "],
            },
            1,
        ))

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {"message": "kmkh"}, 1))

        self.client.force_authenticate(self.u1)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH3",
                "description": "KMKH3",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   2222222222  "],
            },
            1,
        ))

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {"message": "kmkh"}, 1))

        self.client.force_authenticate(self.u1)
        self.printJ(self.get_submissions_inbox())
        self.printJ(self.get_my_submissions())

        # ---------------------------------------------------------------------
        # 10) Allowed-actions endpoint checks:
        #     Different users query allowed action types for submission 1/2.
        #     This should reflect current stage assignment + permissions.
        # ---------------------------------------------------------------------
        self.printJ(self.get_submission_action_types(1))

        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submission_action_types(2))

        self.client.force_authenticate(self.u4)
        self.printJ(self.get_submission_action_types(2))

        self.client.force_authenticate(self.u3)
        self.printJ(self.get_submission_action_types(2))

        # u4 performs REJECT on submission 2 then re-checks allowed actions
        self.client.force_authenticate(self.u4)
        self.printJ(self.send_submission_action(SubmissionActionType.REJECT, {"message": "kmkh"}, 2))
        self.printJ(self.get_submission_action_types(2))

        # Creator views allowed actions + history for submission 2
        self.client.force_authenticate(self.u1)
        self.printJ(self.get_submission_action_types(2))
        self.printJ(self.get_submission_action_history(2))
        self.printJ(self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH3",
                "description": "KMKH3",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["2222222222", "2222222222", "   2222222222  "],
            },
            2,
        ))

        self.client.force_authenticate(self.u4)
        self.printJ(self.send_submission_action(SubmissionActionType.APPROVE, {}, 2))
        self.client.force_authenticate(self.u3)
        self.printJ(self.send_submission_action(SubmissionActionType.APPROVE, {}, 2))

        print(Case.objects.first())