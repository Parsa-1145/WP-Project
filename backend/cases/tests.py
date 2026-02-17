from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from accounts.models import User
from accounts.serializers.fields import NationalIDField
import json
#TODO actual test
class AuthFlowTests(APITestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
                    username="creator",
                    password="pass12345",
                    national_id="1111111111",
                    phone_number="+989121234567",
        )
        self.u1 = User.objects.create_user(
            username="u1",
            password="pass12345",
            national_id="2222222222",
            phone_number="+989121234568",
        )
        self.u2 = User.objects.create_user(
            username="u2",
            password="pass12345",
            national_id="3333333333",
            phone_number="+989121234569",
        )


    def test_complaint_creation(self):
        self.client.force_authenticate(self.creator)
        
        url = reverse("complaint")
        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "complainant_national_ids" : []
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sorted(res.json()["complainants"]), sorted([self.creator.pk]))

        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  "]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sorted(res.json()["complainants"]), sorted([self.creator.pk, self.u1.pk]))

        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  ", "    3333333333     "]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sorted(res.json()["complainants"]), sorted([self.creator.pk, self.u1.pk, self.u2.pk]))


        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "complainant_national_ids" : ["2222222222", "2222222222", "   2222222222  ", "    3333333333     ", "4444444444", " fuck"]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        data = res.json()
        self.assertIn("complainant_national_ids", data)
        self.assertIn("4", data["complainant_national_ids"])
        self.assertIn("5", data["complainant_national_ids"])

        missing = data["complainant_national_ids"]["4"]
        self.assertEqual([NationalIDField.default_error_messages["not_found"].format(value="4444444444")], missing)

    def test_crime_scene_creation(self):
        self.client.force_authenticate(self.creator)

        url = reverse("crime-scene")
        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "witnesses" : []
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "witnesses" : [{"phone_number": "989112405786", "national_id": "   2222222222   "}, {"phone_number": "989112405786", "national_id": "   3333333333   "}]
        }
        res = self.client.post(url, payload, format="json")
        print(res.json())
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "witnesses" : [{"phone_number": "989112405786", "national_id": "22222222222"}]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "witnesses" : [{"phone_number": "989112405786", "national_id": "2222232222"}]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)