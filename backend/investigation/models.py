from django.db import models
from cases.models import Case

# Create your models here.

class DetectiveBoard(models.Model):
    class Meta:
        verbose_name = "Detective Board"
        verbose_name_plural = "Detective Boards"
        
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="detective_board")

    board_json = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON representation of the detective board."
    )



class Verdict(models.Model):
    # Stores the final judgment (Guilty/Not Guilty)
    # Includes the sentence details (punishment) written by the Judge
    pass

class InvestigationResults(models.Model):
    pass

class Suspect(models.Model):
    pass
