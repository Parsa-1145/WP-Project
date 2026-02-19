from django.urls import path
from . import views

urlpatterns = [
    path("mine/", views.SubmissionMineListView.as_view(), name="submission-mine-list"),
    path("inbox/", views.SubmissionInboxListView.as_view(), name="submission-inbox-list"),

    path("", views.SubmissionCreateView.as_view(), name="submission-create"),


    path("<int:pk>/actions/", views.SubmissionActionListCreateView.as_view(), name="submission-action-list-create"),
    path("<int:pk>/actions/types/", views.SubmissionActionTypeGetView.as_view(), name="submission-action-type"),
    path("<int:pk>/", views.SubmissionGetView.as_view(), name="submission-get"),
    path("types/", views.SubmissionTypeListView.as_view(), name="submission-type-list"),
]

