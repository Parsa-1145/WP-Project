import requests
from rest_framework import views, permissions, status
from rest_framework.response import Response
from core import settings
from .models import BailRequest, PaymentTransaction
from django.utils import timezone
from django.shortcuts import redirect,render
from django.db import transaction

class PaymentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        bail_request_id = kwargs.get("pk")
        bail_request = BailRequest.objects.filter(id=bail_request_id, user=user, status=BailRequest.Status.APPROVED).first()
        if not bail_request:
            return Response({"error": "Bail request not found or not approved"}, status=status.HTTP_404_NOT_FOUND)


        try:
            response = requests.post(f"{settings.GATEWAY_BASE_URL}/pg/v4/payment/request.json", json={
                "merchant_id": settings.MERCHANT_ID,
                "amount": bail_request.amount,
                "currency": "IRR",
                "callback_url": settings.PAYMENT_CALLBACK_URL,
                "description": f"Bail payment for user {user.username}",
                "metadata": {
                    "user_id": user.id,
                    "bail_request_id": bail_request.id
                    },
                }, 
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()['data']

        except requests.RequestException as e:
            return Response({"error": "Failed to connect to payment gateway"}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if "code" in response_data and response_data["code"] == 100:
            PaymentTransaction.objects.create(
                user=user,
                amount=bail_request.amount,
                status=PaymentTransaction.Status.PENDING,
                authority=response_data["authority"],
                bail_request=bail_request
            )
            payment_url = f"{settings.GATEWAY_BASE_URL}/pg/StartPay/{response_data['authority']}"
            return Response({"payment_url": payment_url}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Payment gateway returned an error", "details": response_data.get("message", "Unknown error")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        



class PaymentCallbackView(views.APIView):
    permission_classes = [permissions.AllowAny]
    @transaction.atomic
    def get(self, request, *args, **kwargs):
        authority = request.query_params.get("Authority")
        status = request.query_params.get("Status")

        transaction = PaymentTransaction.objects.select_for_update().filter(authority=authority).first()
        if not transaction:
            return render(request, "payment_success.html", {
                    "error": "Transaction not found",
                    "frontend_dashboard_url": settings.FRONT_DASHBOARD_URL
                }
            )

        if transaction.status == PaymentTransaction.Status.COMPLETED:
            return render(request, "payment_success.html", {
                    "ref_id": transaction.ref_id,
                    "frontend_dashboard_url": settings.FRONT_DASHBOARD_URL
                }
            )

        if status and status == "OK":
            try:
                response = requests.post(f"{settings.GATEWAY_BASE_URL}/pg/v4/payment/verify.json", json={
                    "merchant_id": settings.MERCHANT_ID,
                    "authority": authority,
                    "amount": transaction.amount
                    }, 
                    timeout=10
                )
                response.raise_for_status()
                response_data = response.json()['data']

                if "code" in response_data and response_data["code"] in [100, 101]:
                    transaction.status = PaymentTransaction.Status.COMPLETED
                    transaction.completed_at = timezone.now()
                    transaction.gateway_message = response_data.get("message", "")
                    transaction.ref_id = response_data.get("ref_id")
                    transaction.save()
                    return render(request, "payment_success.html", {
                            "ref_id": transaction.ref_id,
                            "frontend_dashboard_url": settings.FRONT_DASHBOARD_URL
                        }
                    )
                else:
                    transaction.status = PaymentTransaction.Status.FAILED
                    transaction.gateway_message = response_data.get("message", "Verification failed by gateway")
                    transaction.save()
            except requests.RequestException:
                transaction.status = PaymentTransaction.Status.FAILED
                transaction.gateway_message = "Gateway connection timeout or error"
                transaction.save()
        else:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.gateway_message = "Payment canceled by the user"
            transaction.save()
        return render(request, "payment_success.html", {
                        "error": transaction.gateway_message,
                        "frontend_dashboard_url": settings.FRONT_DASHBOARD_URL
                    }
                )
    

