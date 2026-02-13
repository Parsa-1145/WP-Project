from django.db import models
from django.contrib.auth.models import AbstractUser
from core import settings
from . import validators as customValidators
# Create your models here.

class User(AbstractUser):
    national_id = models.CharField(
        max_length=10,
        validators=[customValidators.validate_national_id]
    )
    phone_number = models.CharField(
        max_length=13,
        validators=[customValidators.validate_phone_number]
    )

class Role(models.Model):
    pass
