from rest_framework.test import APITestCase
from rest_framework import status
from .models import Evidence
from cases.models import Case
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class EvidenceTests(APITestCase):
    def setUp(self) -> None:
        self.case1 = Case.objects.create(
            title="Saman Bank Robbery",
            description="Investigation of the robbery on Feb 10",
            crime_date=timezone.now()
        )
        self.recorder1 = User.objects.create_user(username="recorder1", password="password123")
        self.list_url = reverse('evidence-list')
        self.evidence = Evidence.objects.create(
            title="Test Vehicle Evidence",
            recorder=self.recorder1,
            description="Test evidence",
            case=self.case1
        )

    def test_evidence_list(self):
        self.client.force_authenticate(user=self.recorder1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Can't see all evidence