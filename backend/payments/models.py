from django.db import models
from core import settings


class BailRequest(models.Model):
    # Represents a request for bail or fine payment (for Level 2 & 3 crimes)
    # Stores the amount determined by the Sergeant
    class Status(models.TextChoices):
        PENDING = 'pending', "Pending"
        APPROVED = 'approved', "Approved"
        REJECTED = 'rejected', "Rejected"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.IntegerField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bail_requests'
    )

    pass

class Reward(models.Model):
    # Represents a reward for a citizen who provided valid info
    # Stores the generated Unique ID and the calculated amount
    pass

class PaymentTransaction(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', "Pending"
        COMPLETED = 'completed', "Completed"
        FAILED = 'failed', "Failed"
        REFUNDED = 'refunded', "Refunded"


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    amount = models.IntegerField()

    authority = models.CharField(max_length=100, unique=True, null=False, blank=False)
    bail_request = models.ForeignKey(
        BailRequest,
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True,
        blank=True
    )
    gateway_message = models.TextField(null=True, blank=True)
    ref_id = models.IntegerField(null=True, blank=True) 



    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.status} - {self.amount} IRR"