from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Subquery
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta

from accounts.models import User
from submissions.models import Submission, SubmissionActionType, SubmissionStatus
from evidence.models import OtherEvidence

from .models import Case, CaseSubmissionLink
from .submissiontypes import CaseStaffingSubmissionType 
import json

class CaseCreationTest(APITestCase):
    @classmethod
    def add_perms(cls, user: User, *codenames):
        for codename in codenames:
            user.user_permissions.add(Permission.objects.get(codename=codename))
    
    @classmethod
    def setUpTestData(cls):
        print("asd")
        cls.u1 = User.objects.create_user(
            username="creator",
            password="pass12345",
            first_name="Case",
            last_name="Creator",
            national_id="1111111111",
            phone_number="+989121234567",
        )
        cls.u2 = User.objects.create_user(
            username="u1",
            password="pass12345",
            first_name="User",
            last_name="One",
            national_id="2222222222",
            phone_number="+989121234568",
        )
        cls.u3 = User.objects.create_user(
            username="u3",
            password="pass12345",
            first_name="User",
            last_name="Three",
            national_id="3333333333",
            phone_number="+989121234569",
        )
        cls.u4 = User.objects.create_user(
            username="u4",
            password="pass12345",
            first_name="User",
            last_name="Four",
            national_id="4444544444",
            phone_number="+989121234569",
        )
        cls.u5 = User.objects.create_user(
            username="u5",
            password="pass12345",
            first_name="User",
            last_name="Five",
            national_id="5555555555",
            phone_number="+989121234569",
        )
        cls.u6 = User.objects.create_user(
            username="u6",
            password="pass12345",
            first_name="User",
            last_name="Six",
            national_id="6666666666",
            phone_number="+989121234569",
        )

        cls.add_perms(cls.u1, "investigate_on_case", "supervise_case")
        cls.add_perms(cls.u2, "complaint_initial_approve")
        cls.add_perms(cls.u3, "complaint_final_approve", "add_crimescene", "approve_crime_scene")
        cls.add_perms(cls.u4, "complaint_initial_approve", "add_crimescene")
        cls.add_perms(cls.u5, "investigate_on_case", "supervise_case")
        cls.add_perms(cls.u6, "supervise_case")


        cls.submission_type_list_url = reverse("submission-type-list")
        cls.submission_inbox_list_url = reverse("submission-inbox-list")
        cls.submission_mine_list_url = reverse("submission-mine-list")
        cls.submission_create_url = reverse("submission-create")


    def send_submission(self, submission_type, payload) -> HttpResponse:
        return self.client.post(
            self.submission_create_url,
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
    
    def get_submission(self, submission_id):
        url = reverse("submission-get", kwargs={"pk": submission_id})
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
            set(response.json()["target"]["complainant_national_ids"]),
            {self.u1.national_id, self.u2.national_id},
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

    def test_submission_get_authorization(self):
        complaint_payload = {
            "title": "KMKH",
            "description": "KMKH",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "complainant_national_ids": ["2222222222"],
        }

        outsider = User.objects.create_user(
            username="outsider",
            password="pass12345",
            national_id="4444444444",
            phone_number="+989121234570",
        )

        self.client.force_authenticate(self.u1)
        response = self.send_submission("COMPLAINT", complaint_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission_id = response.json()["id"]

        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], submission_id)

        self.client.force_authenticate(None)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(outsider)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.u2)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.u4)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.u3)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.u2)
        response = self.send_submission_action(SubmissionActionType.APPROVE, {}, submission_id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.u3)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.u1)
        response = self.get_submission(submission_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_case_assignment_test(self):
        self.client.force_authenticate(self.u1)
        complaint_payload = {
            "title": "Test Title",
            "description": "test description",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "complainant_national_ids": ["2222222222", "3333333333"],
        }
        crime_scene_payload = {
            "title": "Crime Scene A",
            "description": "desc",
            "crime_datetime": "2026-02-17T21:35:00Z",
            "witnesses": [
                {"phone_number": "989112405786", "national_id": "2222222222"},
                {"phone_number": "989112405787", "national_id": "3333333333"},
            ],
        }

        # Case from complaint
        res = self.send_submission("COMPLAINT", payload=complaint_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        complaint_id = res.json()["target"]["id"]

        self.client.force_authenticate(self.u2)
        res = self.send_submission_action("APPROVE", {}, complaint_id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u3)
        res = self.send_submission_action("APPROVE", {}, complaint_id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Case from crime scene
        self.client.force_authenticate(self.u4)
        response = self.send_submission("CRIME_SCENE", crime_scene_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        crime_scene_id = response.json()["id"]

        self.client.force_authenticate(self.u3)
        res = self.send_submission_action("APPROVE", {}, crime_scene_id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        crime_scene_case = Case.objects.get(
            submission_links__submission_id=crime_scene_id,
            submission_links__relation_type=CaseSubmissionLink.RelationType.ORIGIN,
        )

        complaint_case = Case.objects.get(
            submission_links__submission_id=complaint_id,
            submission_links__relation_type=CaseSubmissionLink.RelationType.ORIGIN
        )

        crime_scene_case_acceptance = Submission.objects.get(
            case_link__case_id=crime_scene_case.pk,
            submission_type=CaseStaffingSubmissionType.type_key
        )
        complaint_case_acceptance   = Submission.objects.get(
            case_link__case_id=complaint_case.pk,
            submission_type=CaseStaffingSubmissionType.type_key
        )

        self.assertIsNotNone(complaint_case)
        self.assertIsNotNone(crime_scene_case)
        self.assertIsNotNone(crime_scene_case_acceptance)
        self.assertIsNotNone(complaint_case_acceptance)


        # Check if the acceptance submissions are in the detective inbox
        self.client.force_authenticate(self.u5)
        res = self.get_submissions_inbox()
        self.assertIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])
        self.assertIn(complaint_case_acceptance.pk, [item["id"] for item in res.json()])

        # Check if the acceptance submissions are not in non detective inboxes
        self.client.force_authenticate(self.u4)
        res = self.get_submissions_inbox()
        self.assertNotIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])
        self.assertNotIn(complaint_case_acceptance.pk, [item["id"] for item in res.json()])


        self.client.force_authenticate(self.u2)
        res = self.get_submissions_inbox()
        self.assertNotIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])
        self.assertNotIn(complaint_case_acceptance.pk, [item["id"] for item in res.json()])


        self.client.force_authenticate(self.u3)
        res = self.get_submissions_inbox()
        self.assertNotIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])
        self.assertNotIn(complaint_case_acceptance.pk, [item["id"] for item in res.json()])

        # Detective accepts
        self.client.force_authenticate(self.u5)
        res = self.send_submission_action("ACCEPT", {}, crime_scene_case_acceptance.pk)
        crime_scene_case.refresh_from_db() # wooh that was intresting. this doesnt update automatically
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(crime_scene_case.lead_detective, self.u5)

        # u5 has supervision permission so he should see it
        res = self.get_submissions_inbox()
        self.assertIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])

        # u6 has supervision permission so he should see it
        self.client.force_authenticate(self.u6)
        res = self.get_submissions_inbox()
        self.assertIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])

        # u3 doesnt have supervision permission so he should not see it
        self.client.force_authenticate(self.u3)
        res = self.get_submissions_inbox()
        self.assertNotIn(crime_scene_case_acceptance.pk, [item["id"] for item in res.json()])

        # u5 is the detective and cant supervise
        self.client.force_authenticate(self.u5)
        res = self.send_submission_action("ACCEPT", {}, crime_scene_case_acceptance.pk)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # u6 can be the supervisor
        self.client.force_authenticate(self.u6)
        res = self.send_submission_action("ACCEPT", {}, crime_scene_case_acceptance.pk)
        crime_scene_case.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(crime_scene_case.status, crime_scene_case.Status.OPEN_INVESTIGATION)
        self.assertEqual(crime_scene_case.lead_detective, self.u5)
        self.assertEqual(crime_scene_case.supervisor, self.u6)

        
        # Complaint submission acceptance. U1 is a complainee so they shouldnt be able to be a lead detective
        self.client.force_authenticate(self.u1)
        res = self.get_submissions_inbox()
        self.assertIn(complaint_case_acceptance.pk, [item["id"] for item in res.json()])

        self.client.force_authenticate(self.u1)
        res = self.send_submission_action("ACCEPT", {}, complaint_case_acceptance.pk)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.u5)
        res = self.send_submission_action("ACCEPT", {}, complaint_case_acceptance.pk)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.u1)
        res = self.send_submission_action("ACCEPT", {}, complaint_case_acceptance.pk)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.u6)
        res = self.send_submission_action("ACCEPT", {}, complaint_case_acceptance.pk)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        complaint_case.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(complaint_case.status, complaint_case.Status.OPEN_INVESTIGATION)
        self.assertEqual(complaint_case.lead_detective, self.u5)
        self.assertEqual(complaint_case.supervisor, self.u6)


        complaint_case_acceptance.refresh_from_db()
        crime_scene_case_acceptance.refresh_from_db()
        self.assertEqual(complaint_case_acceptance.status, SubmissionStatus.ACCEPTED)
        self.assertEqual(crime_scene_case_acceptance.status, SubmissionStatus.ACCEPTED)

        # now u5 is the detective for both cases and u6 is their supervisor


class CaseListAccessTest(APITestCase):
    @classmethod
    def add_perms(cls, user: User, *codenames):
        for codename in codenames:
            user.user_permissions.add(Permission.objects.get(codename=codename))

    @classmethod
    def setUpTestData(cls):
        base_dt = timezone.now()

        cls.detective = User.objects.create_user(
            username="detective",
            password="pass12345",
            national_id="7000000001",
            phone_number="+989121111111",
            first_name="Det",
            last_name="One",
        )
        cls.supervisor = User.objects.create_user(
            username="supervisor",
            password="pass12345",
            national_id="7000000002",
            phone_number="+989122222222",
            first_name="Sup",
            last_name="One",
        )
        cls.complainant = User.objects.create_user(
            username="complainant",
            password="pass12345",
            national_id="7000000003",
            phone_number="+989123333333",
            first_name="Comp",
            last_name="One",
        )
        cls.complainant_with_all = User.objects.create_user(
            username="complainant_all",
            password="pass12345",
            national_id="7000000004",
            phone_number="+989124444444",
            first_name="Comp",
            last_name="All",
        )
        cls.viewer = User.objects.create_user(
            username="viewer",
            password="pass12345",
            national_id="7000000005",
            phone_number="+989125555555",
            first_name="View",
            last_name="All",
        )
        cls.outsider = User.objects.create_user(
            username="outsider",
            password="pass12345",
            national_id="7000000006",
            phone_number="+989126666666",
            first_name="Out",
            last_name="Side",
        )

        cls.add_perms(cls.viewer, "view_all_cases")
        cls.add_perms(cls.complainant_with_all, "view_all_cases")

        cls.case_assigned = Case.objects.create(
            title="Assigned Case",
            description="Sensitive details",
            crime_datetime=base_dt,
            lead_detective=cls.detective,
            supervisor=cls.supervisor,
            witnesses=[{"phone_number": "+989120000000", "national_id": cls.complainant.national_id}],
        )
        cls.case_assigned.complainants.set([cls.complainant])

        cls.case_general = Case.objects.create(
            title="General Case",
            description="General details",
            crime_datetime=base_dt + timedelta(hours=1),
            witnesses=[],
        )

        cls.case_complainant_all = Case.objects.create(
            title="Complainant With Permission Case",
            description="Should not leak full details",
            crime_datetime=base_dt + timedelta(hours=2),
            witnesses=[{"phone_number": "+989121234567", "national_id": cls.complainant_with_all.national_id}],
        )
        cls.case_complainant_all.complainants.set([cls.complainant_with_all])

        cls.case_assigned_submission = Submission.objects.create(
            submission_type="COMPLAINT",
            object_id=999999,
            status=SubmissionStatus.PENDING,
            created_by=cls.detective,
        )
        CaseSubmissionLink.objects.create(
            submission=cls.case_assigned_submission,
            case=cls.case_assigned,
            relation_type=CaseSubmissionLink.RelationType.RELATED,
        )
        cls.case_general_submission = Submission.objects.create(
            submission_type="COMPLAINT",
            object_id=999998,
            status=SubmissionStatus.PENDING,
            created_by=cls.viewer,
        )
        CaseSubmissionLink.objects.create(
            submission=cls.case_general_submission,
            case=cls.case_general,
            relation_type=CaseSubmissionLink.RelationType.RELATED,
        )

        cls.case_assigned_evidence = OtherEvidence.objects.create(
            case=cls.case_assigned,
            recorder=cls.detective,
            title="Assigned Case Evidence",
            description="Evidence for assigned case",
        )
        cls.case_general_evidence = OtherEvidence.objects.create(
            case=cls.case_general,
            recorder=cls.viewer,
            title="General Case Evidence",
            description="Evidence for general case",
        )

    def test_full_case_list_visibility(self):
        full_url = reverse("case-list")

        self.client.force_authenticate(self.detective)
        response = self.client.get(full_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({item["id"] for item in response.json()}, {self.case_assigned.id})

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(full_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({item["id"] for item in response.json()}, {self.case_assigned.id})

        self.client.force_authenticate(self.viewer)
        response = self.client.get(full_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            {item["id"] for item in response.json()},
            {self.case_assigned.id, self.case_general.id, self.case_complainant_all.id},
        )

        self.client.force_authenticate(self.outsider)
        response = self.client.get(full_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_complainant_case_list_is_reduced_and_used_for_complainants(self):
        full_url = reverse("case-list")
        complainant_url = reverse("case-complainant-list")

        self.client.force_authenticate(self.complainant)
        response = self.client.get(complainant_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({item["id"] for item in response.json()}, {self.case_assigned.id})
        self.assertSetEqual(
            set(response.json()[0].keys()),
            {"id", "title", "crime_datetime", "status"},
        )

    def test_case_update_allowed_for_detective_and_supervisor(self):
        update_url = reverse("case-update", kwargs={"pk": self.case_assigned.id})
        payload = {
            "title": "Updated Assigned Case",
            "description": "Updated by detective",
            "complainant_national_ids": [self.complainant_with_all.national_id, self.complainant.national_id],
            "witnesses": [
                {"phone_number": "+989121000000", "national_id": self.complainant.national_id},
            ],
        }

        self.client.force_authenticate(self.detective)
        response = self.client.patch(update_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], payload["title"])
        self.assertEqual(
            set(response.json()["complainant_national_ids"]),
            {self.complainant.national_id, self.complainant_with_all.national_id},
        )

        self.case_assigned.refresh_from_db()
        self.assertEqual(self.case_assigned.title, payload["title"])
        self.assertEqual(self.case_assigned.description, payload["description"])
        self.assertEqual(self.case_assigned.witnesses, payload["witnesses"])
        self.assertSetEqual(
            set(self.case_assigned.complainants.values_list("national_id", flat=True)),
            {self.complainant.national_id, self.complainant_with_all.national_id},
        )

        self.client.force_authenticate(self.supervisor)
        response = self.client.patch(
            update_url,
            {"description": "Updated by supervisor"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.case_assigned.refresh_from_db()
        self.assertEqual(self.case_assigned.description, "Updated by supervisor")

    def test_case_update_forbidden_for_non_assignees(self):
        update_url = reverse("case-update", kwargs={"pk": self.case_assigned.id})
        payload = {"title": "Unauthorized update"}

        self.client.force_authenticate(self.viewer)
        response = self.client.patch(update_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.complainant)
        response = self.client.patch(update_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.complainant_with_all)
        response = self.client.patch(update_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_case_evidence_list_access_and_scoping(self):
        url = reverse("case-evidence-list", kwargs={"pk": self.case_assigned.id})

        self.client.force_authenticate(self.detective)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({item["id"] for item in response.json()}, {self.case_assigned_evidence.id})

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({item["id"] for item in response.json()}, {self.case_assigned_evidence.id})

        self.client.force_authenticate(self.outsider)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.complainant)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_case_submission_list_access_and_scoping(self):
        url = reverse("case-submission-list", kwargs={"pk": self.case_assigned.id})

        self.client.force_authenticate(self.detective)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            {item["submission"]["id"] for item in response.json()},
            {self.case_assigned_submission.id},
        )
        self.assertSetEqual(
            {item["relation"] for item in response.json()},
            {CaseSubmissionLink.RelationType.RELATED},
        )

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            {item["submission"]["id"] for item in response.json()},
            {self.case_assigned_submission.id},
        )

        self.client.force_authenticate(self.outsider)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.complainant)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
