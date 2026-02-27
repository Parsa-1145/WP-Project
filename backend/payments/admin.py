from django.contrib import admin
from .models import PaymentTransaction, BailRequest, DataForReward

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "ref_id")
    ordering = ("-created_at",)
    readonly_fields = ("authority", "gateway_message", "ref_id", "created_at", "updated_at", "completed_at", "bail_request", "amount", "user")
    def has_add_permission(self, request):
        return False

@admin.register(BailRequest)
class BailRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "requested_by", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("requested_by__username",)
    ordering = ("-created_at",)


admin.site.register(DataForReward)