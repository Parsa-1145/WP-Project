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
    A workflow item that references a target object created/managed by a specific `submission_type`.
    """
    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ["-created_at"]
    submission_type = models.CharField(
        max_length=64
    )
    submission_type = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="Submission type",
        help_text="Type key used to route validation/handling and resolve the target object.",
    )

    object_id = models.PositiveIntegerField(
        verbose_name="Target object ID",
        help_text="Primary key of the target object created/linked by this submission.",
    )

    status = models.CharField(
        max_length=16,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
        db_index=True,
        verbose_name="Status",
        help_text="Current workflow status of the submission.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Created by",
        help_text="User who created the submission.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
        help_text="Timestamp when the submission was created.",
    )

    current_stage = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Current stage",
        help_text="0-based index of the active workflow stage for this submission.",
    )

class SubmissionAction(models.Model):
    """
    An immutable event in a submission’s workflow history (e.g., SUBMIT, APPROVE, REJECT, RESUBMIT).
    Stores any action-specific data in `payload`.
    """

    submission = models.ForeignKey(
        Submission,
        related_name="actions_history",
        on_delete=models.CASCADE,
        verbose_name="Submission",
        help_text="Submission this action belongs to.",
    )

    action_type = models.CharField(
        max_length=32,
        choices=SubmissionActionType.choices,
        verbose_name="Action type",
        help_text="Workflow action performed on the submission.",
    )

    payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Payload",
        help_text="Action-specific data. Structure depends on `action_type` (and possibly submission_type).",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submission_actions",
        verbose_name="Created by",
        help_text="User who performed this action.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Created at",
        help_text="Timestamp when the action was created.",
    )

    class Meta:
        verbose_name = "Submission action"
        verbose_name_plural = "Submission actions"
        ordering = ["-created_at"]


class SubmissionStage(models.Model):
    """
    A workflow stage for a submission. Each stage is assigned to either a specific user
    (`target_user`) or to anyone holding a permission (`target_permission`).
    """

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="stages",
        verbose_name="Submission",
        help_text="Submission this stage belongs to.",
    )

    # Targets
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="targeted_submission_stages",
        blank=True,
        null=True,
        verbose_name="Target user",
        help_text="If set, only this user can act on this stage (unless permission-based access is also granted).",
    )

    target_permission = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Target permission",
        help_text='Permission codename required to act on this stage (e.g., "app_label.codename").',
    )

    order = models.PositiveIntegerField(
        null=False,
        blank=False,
        verbose_name="Order",
        help_text="0-based stage index. Must be contiguous per submission starting at 0.",
    )

    allowed_actions = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Allowed actions",
        help_text="List of action type strings permitted at this stage (e.g., ['APPROVE', 'REJECT']).",
    )

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