from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from accounts.models import User
from accounts.serializers.fields import NationalIDField
from django.contrib.auth.models import Permission
from django.http import HttpResponse
import json
#TODO actual test
class AuthFlowTests(APITestCase):

    def add_perms(self, user:User, *codenames):
        for c in codenames:
            print(c)
            user.user_permissions.add(Permission.objects.get(codename=c))

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
            username="u2",
            password="pass12345",
            national_id="3333333333",
            phone_number="+989121234569",
        )

        self.add_perms(self.u2, "first_complaint_review")
        self.add_perms(self.u3, "final_complaint_review", "create_crime_scene")

        self.submission_type_list_url            = reverse("submission-type-list")
        self.submission_inbox_list_url           = reverse("submission-inbox-list")
        self.submission_mine_list_create_url     = reverse("submission-mine-list-create")


    def send_submission(self, submission_type, payload) -> HttpResponse:
        return self.client.post(self.submission_mine_list_create_url, data={"submission_type":submission_type, "payload": payload}, format="json")

    
    def get_submissions(self):
        return self.client.get(self.submission_inbox_list_url, format="json")

    def printJ(self, response: HttpResponse):
        print(json.dumps(response.json(), indent=3))

    def test_complaint_creation(self):
        self.client.force_authenticate(self.u1)
        res = self.client.get(self.submission_type_list_url)
        print(res.json())
        
        self.client.force_authenticate(self.u2)
        res = self.client.get(self.submission_type_list_url)
        print(res.json())

        self.client.force_authenticate(self.u3)
        res = self.client.get(self.submission_type_list_url)
        print(res.json())

        self.client.force_authenticate(self.u1)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  "]
            }
        )
        self.printJ(res)
        
        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "complainant_national_ids" : ["2222222222", "2222222222", "   3333333333  "]
            }
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "complainant_national_ids" : ["2222222222", "2222222222", "   4444444444  "]
            }
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="COMPLAINT",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "complainant_national_ids" : ["2222222222", "2222222222", "   4444444444  ", "  555555 5"]
            }
        )
        self.printJ(res)

        self.printJ(self.get_submissions())
        self.client.force_authenticate(self.u2)
        self.printJ(self.get_submissions())
        self.client.force_authenticate(self.u3)
        self.printJ(self.get_submissions())

        self.client.force_authenticate(self.u3)
        res = self.send_submission(
            submission_type="CRIME_SCENE",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "witnesses" : [{"phone_number": "989112405786", "national_id": "   2222222222   "}, {"phone_number": "989112405786", "national_id": "   3333333333   "}]
            }
        )
        self.printJ(res)

        res = self.send_submission(
            submission_type="CRIME_SCENE",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "witnesses" : [{"phone_number": "989112405786", "national_id": "2222222222"}, {"phone_number": "989112405786", "national_id": "2222232222"}]
            }
        )
        self.printJ(res)

        self.client.force_authenticate(self.u2)
        res = self.send_submission(
            submission_type="CRIME_SCENE",
            payload={
                "title": "KMKH",
                "description": "KMKH",
                "witnesses" : [{"phone_number": "989112405786", "national_id": "2222222222"}, {"phone_number": "989112405786", "national_id": "2222232222"}]
            }
        )
        self.printJ(res)
        # self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(sorted(res.json()["complainants"]), sorted([self.creator.pk]))

        # payload = {
        #     "title" : "KMKH",
        #     "description" : "KMKH",
        #     "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  "]
        # }
        # res = self.client.post(url, payload, format="json")
        # self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(sorted(res.json()["complainants"]), sorted([self.creator.pk, self.u1.pk]))

        # payload = {
        #     "title" : "KMKH",
        #     "description" : "KMKH",
        #     "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  ", "    3333333333     "]
        # }
        # res = self.client.post(url, payload, format="json")
        # self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(sorted(res.json()["complainants"]), sorted([self.creator.pk, self.u1.pk, self.u2.pk]))


        # payload = {
        #     "title" : "KMKH",
        #     "description" : "KMKH",
        #     "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  ", "    3333333333     ", "4444444444", " fuck"]
        # }
        # res = self.client.post(url, payload, format="json")
        # self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # data = res.json()
        # self.assertIn("complainant_national_ids", data)
        # self.assertIn("4", data["complainant_national_ids"])
        # self.assertIn("5", data["complainant_national_ids"])

        # missing = data["complainant_national_ids"]["4"]
        # self.assertEqual([NationalIDField.default_error_messages["not_found"].format(value="4444444444")], missing)

    # def test_crime_scene_creation(self):
    #     self.client.force_authenticate(self.creator)

    #     url = reverse("crime-scene")
    #     payload = {
    #         "title" : "KMKH",
    #         "description" : "KMKH",
    #         "witnesses" : []
    #     }
    #     res = self.client.post(url, payload, format="json")
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    #     payload = {
    #         "title" : "KMKH",
    #         "description" : "KMKH",
    #         "witnesses" : [{"phone_number": "989112405786", "national_id": "   2222222222   "}, {"phone_number": "989112405786", "national_id": "   3333333333   "}]
    #     }
    #     res = self.client.post(url, payload, format="json")
    #     print(res.json())
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    #     payload = {
    #         "title" : "KMKH",
    #         "description" : "KMKH",
    #         "witnesses" : [{"phone_number": "989112405786", "national_id": "22222222222"}]
    #     }
    #     res = self.client.post(url, payload, format="json")
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    #     payload = {
    #         "title" : "KMKH",
    #         "description" : "KMKH",
    #         "witnesses" : [{"phone_number": "989112405786", "national_id": "2222232222"}]
    #     }
    #     res = self.client.post(url, payload, format="json")
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)