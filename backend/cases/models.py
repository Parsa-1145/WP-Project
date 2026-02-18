from django.db import models
from django.contrib.auth.models import AbstractUser
from core import settings

class Case(models.Model):
    class CrimeLevel(models.TextChoices):
        CRITICAL = 'CR', "Critical"
        LEVEL_3 = 'L3', "Level 3"
        LEVEL_2 = 'L2', "Level 2"
        LEVEL_1 = 'L1', "Level 1"

    class Status(models.TextChoices):
        OPEN_INVESTIGATION = 'open'
        SOLVED = 'solved'
        CLOSED = 'closed'

    title = models.CharField(max_length=255)
    description = models.TextField()
    complainants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='filed_cases'
    )
    crime_level = models.CharField(
        max_length=2, 
        choices=CrimeLevel.choices, 
        default=CrimeLevel.LEVEL_3
    )
    lead_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )
    witnesses = models.JSONField(
        blank=True,
        default=list
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.OPEN_INVESTIGATION
    )
    crime_datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class Complaint(models.Model):
    class Meta:
        permissions = [
            ("first_complaint_review", "Can approve complaint submissions"),
            ("final_complaint_review", "Can approve the approval of a complaint submissions"),
        ]

    title = models.CharField(
        blank=False,
        null=False,
        default="Title"
    )
    description = models.TextField(
        blank=False,
        null=False,
        default="Title"
    )
    crime_datetime = models.DateTimeField(
        auto_now=False,
        blank=False,
        null=False
    )
    
    complainants = models.ManyToManyField(
        settings.AUTH_USER_MODEL
    )


class CrimeScene(models.Model):
    class Meta:
        permissions = [
            ("create_crime_scene", "Can create crime scene"),
            ("approve_crime_scene", "Can approve crime scene")
        ]

    title = models.CharField(
        blank=False,
        null=False,
        default="Title"
    )
    description = models.TextField(
        blank=False,
        null=False,
        default="Title"
    )
    crime_datetime = models.DateTimeField(
        auto_now=False,
        blank=False,
        null=False
    )
    witnesses = models.JSONField(
        blank=True,
        default=list
    )