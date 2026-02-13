from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

User = get_user_model()

#TODO actual test
class AuthFlowTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse("signup")
        self.login_url = reverse("login")
        self.refresh_url = reverse("token_refresh")

    def test_signup_login_refresh(self):
        signup_payload = {"username": "alice", "password": "strongpassword123", "email":"parsazamiri@gmail.com", "first_name": "Parsa", "last_name": "Zamiri", "national_id": "2581801980", "phone_number": "09112405786"}
        r = self.client.post(self.signup_url, signup_payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="alice").exists())

        login_payload = {"username": "alice", "password": "strongpassword123"}
        r = self.client.post(self.login_url, login_payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

        access = r.data["access"]
        refresh = r.data["refresh"]

        r = self.client.post(self.refresh_url, {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)

    def test_login_wrong_password_fails(self):
        User.objects.create_user(username="bob", password="correctpassword123")

        r = self.client.post(
            self.login_url,
            {"username": "bob", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", r.data)
