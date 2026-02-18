from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from accounts.models import User
from accounts.serializers.fields import NationalIDField
from .submissiontypes.registry import SUBMISSION_TYPES
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
        
        url = reverse("submission-create")
        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "complainant_national_ids" : []
        }
        request = {
            "submission_type" : "COMPLAINT",
            "payload": payload
        }
        res = self.client.post(url, request, format="json")
        print(json.dumps(res.json(), indent=3))
        print(SUBMISSION_TYPES)

    def test_crime_scene_creation(self):
        self.client.force_authenticate(self.creator)

        url = reverse("submission-create")
        payload = {
            "title" : "KMKH",
            "description" : "KMKH",
            "witnesses" : []
        }