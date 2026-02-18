from django.contrib import admin

from .models import *

admin.site.register(Evidence)
admin.site.register(WitnessEvidence)
admin.site.register(BioEvidence)
admin.site.register(BioEvidenceImage)
admin.site.register(VehicleEvidence)
admin.site.register(IdentityEvidence)
admin.site.register(OtherEvidence)