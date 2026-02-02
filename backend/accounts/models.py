from django.db import models
from django.contrib.auth.models import AbstractUser
from core import settings
# Create your models here.

class User(AbstractUser):
    pass

class Role(models.Model):
    pass



# --------------------- Evidence



from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

