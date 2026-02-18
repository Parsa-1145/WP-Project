from django.db import models
from django.contrib.auth.models import AbstractUser
from core import settings
from submissions.models import Submission

class Case(models.Model):
    class Meta:
        permissions = {

        }
    class CrimeLevel(models.TextChoices):
        CRITICAL = 'CR', "Critical"
        LEVEL_3 = 'L3', "Level 3"
        LEVEL_2 = 'L2', "Level 2"
        LEVEL_1 = 'L1', "Level 1"

    class Status(models.TextChoices):
        OPEN_INVESTIGATION = 'open'
        SOLVED = 'solved'
        CLOSED = 'closed'

    title = models.CharField(
        blank=False,
        null=False
    )
    description = models.TextField(
        blank=False,
        null=False
    )
    crime_datetime = models.DateTimeField(
        blank=False,
        null=False,
        auto_now=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    complainants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='filed_cases',
        blank=True
    )
    witnesses = models.JSONField(
        blank=True,
        null=False,
        default=list
    )

    submissions = models.ManyToManyField(
        Submission,
        through="CaseSubmissionLink",
        related_name="case_set",
        blank=True,
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
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.OPEN_INVESTIGATION
    )

    def __str__(self):
        complainants_str = ", ".join(
            str(u) for u in self.complainants.all()
        ) or "None"

        return (
            f"Case({self.id}):\n"
            f"    title: {self.title}\n"
            f"    description: {self.description}\n"
            f"    crime_datetime: {self.crime_datetime}\n"
            f"    crime_level: {self.get_crime_level_display()} ({self.crime_level})\n"
            f"    status: {self.get_status_display() if hasattr(self, 'get_status_display') else self.status} ({self.status})\n"
            f"    lead_detective: {self.lead_detective or 'None'}\n"
            f"    complainants: {complainants_str}\n"
            f"    witnesses_count: {len(self.witnesses or [])}\n"
        )

class CaseSubmissionLink(models.Model):
    class RelationType(models.TextChoices):
        ORIGIN="ORIGIN"
        EVIDENCE="EVIDENCE"
        RELATED="RELATED"
    
    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name="case_link",
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="submission_links",
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RelationType.choices,
        default=RelationType.RELATED,
    )

class Complaint(models.Model):
    class Meta:
        permissions = [
            ("complaint_initial_approve", "Can approve complaint submissions"),
            ("complaint_final_approve", "Can approve the approval of a complaint submissions"),
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