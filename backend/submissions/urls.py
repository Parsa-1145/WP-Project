from django.urls import path
from . import views

urlpatterns = [
    path("mine/", views.SubmissionListCreateView.as_view(), name="submission-mine-list-create"),
    path("inbox/", views.SubmissionInboxListView.as_view(), name="submission-inbox-list"),

    path("<int:pk>/actions/", views.SubmissionActionCreateView.as_view(), name="submission-action-create"),
    path("submission-types/", views.SubmissionTypeListView.as_view(), name="submission-type-list"),
]