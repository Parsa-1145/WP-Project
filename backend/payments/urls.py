from django.urls import path
from . import views

urlpatterns = [
    path("pay/<int:pk>/", views.PaymentView.as_view(), name="payment-request"),
    path("callback/", views.PaymentCallbackView.as_view(), name="payment-callback"),

]