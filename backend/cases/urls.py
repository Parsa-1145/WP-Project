from django.urls import path
from .views import ComplaintCreateView, CrimeSceneCreateView

urlpatterns = [
    path("complaint/", ComplaintCreateView.as_view(), name="complaint"),
    path("crime-scene/", CrimeSceneCreateView.as_view(), name="crime-scene"),
]