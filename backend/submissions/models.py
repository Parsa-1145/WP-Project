# approvals/models.py
from core import settings
from django.db import models
from django.core.exceptions import ValidationError

class SubmissionStatus(models.TextChoices):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class SubmissionEventType(models.TextChoices):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCLE"

class Submission(models.Model):
    """
    Docstring for Request
    """
    submission_type = models.CharField(
        max_length=64
    )
    object_id = models.PositiveIntegerField()

    status = models.CharField(max_length=16, choices=SubmissionStatus.choices, default=SubmissionStatus.PENDING)
    current_stage=models.IntegerField(default=0)

class SubmissionEvent(models.Model):
    """
    Docstring for RequestEvent
    """
    submission = models.ForeignKey(Submission, related_name="events", on_delete=models.CASCADE)
    event_type = models.CharField(choices=SubmissionEventType.choices, null=False, blank=False)
    message = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
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
    target_permissions = models.CharField(max_length=64)

    order = models.PositiveIntegerField(null=False, blank=False)

    class Meta:
        constraints = [
            # each submission can only have one stage of order k
            models.UniqueConstraint(
                fields=["submission", "order"],
                name="uniq_stage_order_per_submission",
            ),
            # each stage should have target_user or target_group
            models.CheckConstraint(
                condition=models.Q(target_user__isnull=False) | models.Q(target_permissions__isnull=False),
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

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)