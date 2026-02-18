from django.db import models
from django.contrib.auth.models import AbstractUser
from core import settings

class Case(models.Model):
    """
    این مدل نماینده پرونده‌های پلیس است.
    مسئولیت: نگهداری وضعیت حقوقی، سطح جرم و گردش کار پرونده.
    """

    class CrimeLevel(models.TextChoices):
        CRITICAL = 'CR', "Critical"
        LEVEL_3 = 'L3', "Level 3"
        LEVEL_2 = 'L2', "Level 2"
        LEVEL_1 = 'L1', "Level 1"

    # طبق بخش ۱۰۴ و ۲۰۴ (روندهای تشکیل پرونده) [cite: 153, 154, 198]
    class Status(models.TextChoices):
        OPEN_INVESTIGATION = 'open'
        SOLVED = 'solved'
        CLOSED = 'closed'

    # شناسه پرونده (غیر از ID دیتابیس، برای نمایش به کاربر)
    case_number = models.CharField(max_length=20, unique=True, editable=False)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    crime_level = models.CharField(
        max_length=2, 
        choices=CrimeLevel.choices, 
        default=CrimeLevel.LEVEL_3
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.OPEN_INVESTIGATION
    )

    # --- 3. Relations (ارتباطات) ---
    
    # چه کسی پرونده را ثبت کرده؟ (می‌تواند شهروند یا پلیس باشد) [cite: 151, 163]
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='reported_cases'
    )

    # کارآگاه مسئول پرونده (پس از تشکیل پرونده مشخص می‌شود) [cite: 198]
    lead_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )

    complainants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
<<<<<<< HEAD
        through='Complaint',
=======
>>>>>>> request
        related_name='filed_cases'
    )

    witnesses = models.JSONField(
        blank=True
    )

    # --- 4. Metadata ---
    crime_date = models.DateTimeField() # [cite: 165]
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case_number} - {self.title}"

    def save(self, *args, **kwargs):
        # تولید خودکار شماره پرونده اگر وجود نداشته باشد
        if not self.case_number:
            import uuid
            self.case_number = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

class Complaint(models.Model):
<<<<<<< HEAD
    title = models.CharField(max_length=255)
    description = models.TextField()

    case = models.ForeignKey(
        Case, 
        on_delete=models.CASCADE,
        related_name='complaints_list' 
    )

    complainant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filed_complaints'
=======
    class Meta:
        permissions = [
            ("first_complaint_review", "Can approve complaint submissions"),
            ("final_complaint_review", "Can approve the approval of a complaint submissions"),
        ]
    title = models.CharField()
    description = models.TextField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_complaints",
>>>>>>> request
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

    title = models.CharField(max_length=10)
    description = models.TextField(max_length=10)
    witnesses = models.JSONField(
        blank=True
    )
