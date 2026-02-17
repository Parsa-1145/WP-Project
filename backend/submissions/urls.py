from django.urls import path
from . import views

urlpatterns = [
    path("mine/", views.SubmissionListCreateView.as_view(), name="submission-mine-list-create"),
    path("inbox/", views.SubmissionListCreateView.as_view(), name="submission-inbox-list"),
    path("submission-types/", views.SubmissionTypeListView.as_view(), name="submission-type-list"),
]