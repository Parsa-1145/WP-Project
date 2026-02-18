from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from submissions.models import Submission, SubmissionActionType, SubmissionStatus

from .models import Case
import json

class AuthFlowTests(APITestCase):
    def add_perms(self, user: User, *codenames):
        for codename in codenames:
            user.user_permissions.add(Permission.objects.get(codename=codename))

    def setUp(self):
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

        self.add_perms(self.u2, "complaint_initial_approve")
        self.add_perms(self.u3, "complaint_final_approve", "add_crimescene", "approve_crime_scene")
        self.add_perms(self.u4, "complaint_initial_approve", "add_crimescene")

        self.submission_type_list_url = reverse("submission-type-list")
        self.submission_inbox_list_url = reverse("submission-inbox-list")
        self.submission_mine_list_create_url = reverse("submission-mine-list-create")

    def send_submission(self, submission_type, payload) -> HttpResponse:
        return self.client.post(
            self.submission_mine_list_create_url,
            data={"submission_type": submission_type, "payload": payload},
            format="json",
        )

    def send_submission_action(
        self,
        action_type: SubmissionActionType,
        payload,
        submission_id,
    ) -> HttpResponse:
        url = reverse("submission-action-list-create", kwargs={"pk": submission_id})
        return self.client.post(
            url,
            data={"action_type": action_type, "payload": payload},
            format="json",
        )

    def get_submissions_inbox(self):
        return self.client.get(self.submission_inbox_list_url, format="json")

    def get_submission_action_types(self, submission_id):
        url = reverse("submission-action-type", kwargs={"pk": submission_id})
        return self.client.get(url, format="json")

    def assert_type_keys(self, user, expected_keys):

        self.client.force_authenticate(user)
        response = self.client.get(self.submission_type_list_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            {item["key"] for item in response.json()["types"]},
            set(expected_keys),
        )

    def printJ(self, data):
        print(json.dumps(data.json(), indent=2))

    def test_complaint_creation(self):
        initial_case_count = Case.objects.count()
        self.assert_type_keys(self.u1, {"COMPLAINT"})
        self.assert_type_keys(self.u2, {"COMPLAINT"})
        self.assert_type_keys(self.u3, {"COMPLAINT", "CRIME_SCENE"})

        self.client.force_authenticate(self.u1)
        complaint_payload = {
            "title": "KMKH",
            "description": "KMKH",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "complainant_national_ids": ["2222222222", "2222222222", "   2222222222  "],
        }
        response = self.send_submission("COMPLAINT", complaint_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        complaint_submission_id = response.json()["id"]
        self.assertEqual(response.json()["submission_type"], "COMPLAINT")
        self.assertEqual(response.json()["status"], SubmissionStatus.PENDING)
        self.assertSetEqual(
            set(response.json()["target"]["complainants"]),
            {self.u1.id, self.u2.id},
        )

        invalid_complaint_payload = {
            "title": "KMKH",
            "description": "KMKH",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "complainant_national_ids": ["2222222222", "2222222222", "   4444444444  ", "  555555 5"],
        }
        response = self.send_submission("COMPLAINT", invalid_complaint_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        national_id_errors = response.json()["payload"][0]["complainant_national_ids"]
        self.assertIn("2", national_id_errors)
        self.assertIn("3", national_id_errors)

        self.client.force_authenticate(self.u2)

        response = self.get_submissions_inbox()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(complaint_submission_id, [item["id"] for item in response.json()])

        self.client.force_authenticate(self.u3)
        response = self.get_submissions_inbox()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(complaint_submission_id, [item["id"] for item in response.json()])

        self.client.force_authenticate(self.u1)
        response = self.send_submission_action(SubmissionActionType.APPROVE, {}, complaint_submission_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.u2)
        response = self.send_submission_action(SubmissionActionType.APPROVE, {}, complaint_submission_id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u3)
        response = self.get_submission_action_types(complaint_submission_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            set(response.json()["actions"]),
            {SubmissionActionType.REJECT, SubmissionActionType.APPROVE},
        )

        response = self.send_submission_action(
            SubmissionActionType.REJECT,
            {"message": "needs fixes"},
            complaint_submission_id,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u2)
        response = self.send_submission_action(
            SubmissionActionType.REJECT,
            {"message": "still wrong"},
            complaint_submission_id,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u1)
        response = self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            invalid_complaint_payload,
            complaint_submission_id,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.send_submission_action(
            SubmissionActionType.RESUBMIT,
            {
                "title": "KMKH2",
                "description": "KMKH2",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "complainant_national_ids": ["3333333333", "2222222222"],
            },
            complaint_submission_id,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u2)
        response = self.send_submission_action(SubmissionActionType.APPROVE, {}, complaint_submission_id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u3)
        response = self.send_submission_action(SubmissionActionType.APPROVE, {}, complaint_submission_id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get(pk=complaint_submission_id)
        self.assertEqual(submission.status, SubmissionStatus.APPROVED)

        self.assertEqual(Case.objects.count(), initial_case_count+1)

    def test_crime_scene_workflow(self):
        crime_scene_payload = {
            "title": "Crime Scene A",
            "description": "desc",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "witnesses": [
                {"phone_number": "989112405786", "national_id": "2222222222"},
                {"phone_number": "989112405787", "national_id": "3333333333"},
            ],
        }

        initial_case_count = Case.objects.count()

        self.client.force_authenticate(self.u1)
        response = self.send_submission("CRIME_SCENE", crime_scene_payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.u4)
        response = self.send_submission("CRIME_SCENE", crime_scene_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        crime_scene_submission_id = response.json()["id"]
        self.assertEqual(response.json()["status"], SubmissionStatus.PENDING)

        self.client.force_authenticate(self.u2)
        response = self.send_submission_action(
            SubmissionActionType.APPROVE,
            {},
            crime_scene_submission_id,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.u3)
        response = self.send_submission_action(
            SubmissionActionType.APPROVE,
            {},
            crime_scene_submission_id,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        approved_submission = Submission.objects.get(pk=crime_scene_submission_id)
        self.assertEqual(approved_submission.status, SubmissionStatus.APPROVED)
        self.assertEqual(Case.objects.count(), initial_case_count + 1)

        response = self.send_submission(
            "CRIME_SCENE",
            {
                "title": "Crime Scene B",
                "description": "desc",
                "crime_datetime": "2026-02-17T21:35:00Z",
                "witnesses": [
                    {"phone_number": "989112405788", "national_id": "2222222222"},
                    {"phone_number": "989112405789", "national_id": "3333333333"},
                ],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], SubmissionStatus.APPROVED)

        auto_approved_submission = Submission.objects.get(pk=response.json()["id"])
        self.assertEqual(auto_approved_submission.status, SubmissionStatus.APPROVED)
        self.assertEqual(Case.objects.count(), initial_case_count + 2)
