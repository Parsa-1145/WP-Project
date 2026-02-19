from django.contrib import admin

from .models import *

admin.site.register(Submission)
admin.site.register(SubmissionAction)
admin.site.register(SubmissionStage)
