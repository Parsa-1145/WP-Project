from django.contrib import admin
from .models import PaymentTransaction, BailRequest

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "ref_id")
    ordering = ("-created_at",)

@admin.register(BailRequest)
class BailRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "requested_by", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("requested_by__username",)
    ordering = ("-created_at",)
