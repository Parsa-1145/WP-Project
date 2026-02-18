# approvals/models.py
from core import settings
from django.db import models
from django.core.exceptions import ValidationError

class SubmissionStatus(models.TextChoices):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class SubmissionActionType(models.TextChoices):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCLE"
    RESUBMIT = "RESUBMIT"

class Submission(models.Model):
    """
    Docstring for Request
    """
    submission_type = models.CharField(
        max_length=64
    )
    object_id = models.PositiveIntegerField()

    status = models.CharField(max_length=16, choices=SubmissionStatus.choices, default=SubmissionStatus.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    current_stage=models.IntegerField(default=0)

class SubmissionAction(models.Model):
    """
    Docstring for RequestEvent
    """
    submission = models.ForeignKey(Submission, related_name="actions_history", on_delete=models.CASCADE, blank=False, null=False)
    action_type = models.CharField(choices=SubmissionActionType.choices, null=False, blank=False)
    payload = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class SubmissionStage(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="stages",
    )

    # Targets
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    target_permission = models.CharField(max_length=128, blank=True, null=True)

    order = models.PositiveIntegerField(null=False, blank=False)
    
    allowed_actions = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "order"],
                name="uniq_stage_order_per_submission",
            ),
            models.CheckConstraint(
                condition=models.Q(target_user__isnull=False) | models.Q(target_permission__isnull=False),
                name="stage_has_target_user_or_group",
            ),
        ]
        ordering = ["submission_id", "order"]

    def clean(self):
        super().clean()

        if not self.submission_id or self.order is None:
            return

        existing_orders = list(
            SubmissionStage.objects
            .filter(submission_id=self.submission_id)
            .exclude(pk=self.pk)
            .values_list("order", flat=True)
        )
        orders = sorted(existing_orders + [self.order])

        if orders and orders != list(range(0, len(orders))):
            raise ValidationError({"order": "Stage orders must be contiguous starting at 0."})
        
        allowed = {c for c, _ in SubmissionActionType.choices}

        v = self.allowed_actions
        if v is None:
            raise ValidationError({"allowed_actions": "Must be a list of action type strings."})

        if not isinstance(v, list):
            raise ValidationError({"allowed_actions": "Must be a list."})

        if not all(isinstance(x, str) for x in v):
            raise ValidationError({"allowed_actions": "All items must be strings."})

        invalid = [x for x in v if x not in allowed]
        if invalid:
            raise ValidationError({"allowed_actions": f"Invalid action types: {invalid}. Allowed: {sorted(allowed)}"})

        if len(set(v)) != len(v):
            raise ValidationError({"allowed_actions": "Duplicate action types are not allowed."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)