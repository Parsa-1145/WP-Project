from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Evidence(models.Model):
    """
    Parent model for all evidence types.
    Implements requirements from Section 3.4.
    """
    # Relation to the Case app
    case = models.ForeignKey(
        'cases.Case', 
        on_delete=models.CASCADE, 
        related_name='evidences',
        verbose_name=_("Relevant Case")
    )
    
    # The person who recorded this evidence
    recorder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_evidences',
        verbose_name=_("Recorder")
    )

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date Recorded"))

    def __str__(self):
        return f"{self.title} ({self.get_evidence_type_display()})"

    def get_evidence_type_display(self):
        """
        Helper method to identify evidence type in Admin/UI.
        """
        if hasattr(self, 'witnessevidence'): return 'Witness'
        if hasattr(self, 'bioevidence'): return 'Bio/Medical'
        if hasattr(self, 'vehicleevidence'): return 'Vehicle'
        if hasattr(self, 'identityevidence'): return 'Identity'
        return 'Other'


class WitnessEvidence(Evidence):
    """
    Implements Section 1.3.4: Transcript of witness statements, 
    local reports, or media files.
    """
    media_file = models.FileField(
        upload_to='evidence/witness/', 
        null=True, 
        blank=True
    )
    
    transcript = models.TextField(
        null=True, 
        blank=True
    )


class BioEvidence(Evidence):
    """
    Implements Section 2.3.4: Biological evidence.
    Refactored to support multiple images via BioEvidenceImage model.
    """
    # Removed the single 'image' field from here.
    
    coroner_result = models.TextField(
        null=True, 
        blank=True
    )
    
    is_verified = models.BooleanField(
        default=False
    )

class BioEvidenceImage(models.Model):
    """
    Allows multiple images for a single BioEvidence record.
    """
    evidence = models.ForeignKey(
        BioEvidence,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='evidence/bio/'
    )

    caption = models.CharField(
        max_length=255, 
        blank=True, 
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

class VehicleEvidence(Evidence):
    """
    Implements Section 3.3.4: Vehicle details found at the scene.
    """
    model_name = models.CharField(max_length=100, verbose_name=_("Car Model"))
    color = models.CharField(max_length=50, verbose_name=_("Color"))
    
    # Logic: Either Plate OR Serial Number (VIN)
    plate_number = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        verbose_name=_("License Plate")
    )
    
    serial_number = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name=_("Serial Number (VIN)")
    )

    class Meta:
        verbose_name = _("Vehicle Evidence")
        verbose_name_plural = _("Vehicle Evidences")

    def clean(self):
        """
        Enforces business logic from Section 3.3.4:
        A vehicle cannot have both a plate number and a serial number simultaneously.
        """
        if self.plate_number and self.serial_number:
            raise ValidationError(
                _("A vehicle cannot have both a license plate and a serial number.")
            )
        
        if not self.plate_number and not self.serial_number:
            raise ValidationError(
                _("Vehicle must have at least a license plate or a serial number.")
            )
        
class IdentityEvidence(Evidence):
    """
    Implements Section 4.3.4: Identity documents found.
    Uses Key-Value storage for flexibility.
    """
    full_name = models.CharField(
        max_length=255, 
        verbose_name=_("Owner Full Name")
    )

    # JSONField allows storing arbitrary key-value pairs 
    # (e.g., {"father_name": "John", "national_id": "123"})
    details = models.JSONField(
        default=dict, 
        verbose_name=_("Details (Key-Value)")
    )

    class Meta:
        verbose_name = _("Identity Evidence")
        verbose_name_plural = _("Identity Evidences")