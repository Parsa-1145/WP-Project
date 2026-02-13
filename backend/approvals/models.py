# approvals/models.py
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

class ApprovalStatus(models.TextChoices):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class ApprovalRequest(models.Model):
    # attach to any domain object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")

    status = models.CharField(max_length=16, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)

    # who must act (can be role-based or user-based; start simple)
    required_role = models.CharField(max_length=64)  # e.g. "LOW_RANK", "SHERIFF"
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="approvals_created",
                                   on_delete=models.PROTECT)
    acted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 related_name="approvals_acted", on_delete=models.SET_NULL)

    rejection_message = models.TextField(blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=0)  # 0 means "no limit"

class ApprovalEvent(models.Model):
    request = models.ForeignKey(ApprovalRequest, related_name="events", on_delete=models.CASCADE)
    from_status = models.CharField(max_length=16)
    to_status = models.CharField(max_length=16)
    message = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)