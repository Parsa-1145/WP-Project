from django.urls import path
from . import views

urlpatterns = [
    path("", views.CaseListView.as_view(), name="case-list"),
    path("complainant/", views.ComplainantCaseListView.as_view(), name="case-complainant-list"),
    path("<int:pk>/evidences/", views.CaseEvidenceListView.as_view(), name="case-evidence-list"),
    path("<int:pk>/submissions/", views.CaseSubmissionListView.as_view(), name="case-submission-list"),
    path("<int:pk>/", views.CaseUpdateView.as_view(), name="case-update"),
    path("<int:pk>/detective-board/", views.DetectiveBoardUpdateView.as_view(), name="case-detective-board"),
]
