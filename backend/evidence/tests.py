from rest_framework.test import APITestCase
from rest_framework import status
from .models import Evidence
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class EvidenceTests(APITestCase):
    def setUp(self) -> None:
        self.recorder1 = User.objects.create_user(username="recorder1", password="password123")
        self.list_url = reverse('evidence-list')
        self.evidence = Evidence.objects.create(
            title="Test Vehicle Evidence",
            recorder=self.recorder1,
            description="Test evidence",
        )

    def test_evidence_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.evidence.id)