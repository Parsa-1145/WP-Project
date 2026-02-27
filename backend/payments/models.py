from django.db import models
from core import settings
import uuid
from django.utils import timezone


class BailRequest(models.Model):
    # Represents a request for bail or fine payment (for Level 2 & 3 crimes)
    # Stores the amount determined by the Sergeant
    class Meta:
        permissions = [
            ("can_approve_bail_request", "Can approve bail requests"),
        ]

    class Status(models.TextChoices):
        PENDING  = 'pending', "Pending"
        APPROVED = 'approved', "Approved"
        REJECTED = 'rejected', "Rejected"
        PAID     = 'paid'    ,  "Paid"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.IntegerField(null=True, blank=True)  
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bail_requests'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    pass




class Reward(models.Model):
    # Represents a reward for a citizen who provided valid info
    # Stores the generated Unique ID and the calculated amount

    class Status(models.TextChoices):
        PENDING = 'PENDING', "Pending"
        CLAIMED = 'CLAIMED', "Claimed"

    unique_code = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rewards'
    )
    submission = models.OneToOneField(
        'submissions.Submission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reward_issued'
    )
    amount = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reward {self.unique_code} - {self.user.username}"

    def claim(self):
        """
        Mark this reward as claimed if it is still pending.
        """
        if self.status == self.Status.CLAIMED:
            raise ValueError("Reward has already been claimed.")
        self.status = self.Status.CLAIMED
        self.claimed_at = timezone.now()
        self.save(update_fields=["status", "claimed_at"])


class DataForReward(models.Model):
    class Meta:
        permissions = [
            ("can_approve_data_reward", "Can approve data for reward submissions"),
        ]
    description = models.TextField()
    reward = models.ForeignKey(
        Reward,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="data_for_rewards",
    )


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