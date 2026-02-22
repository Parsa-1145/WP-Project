from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None,
          {"fields": ("username", "email", "password")}
        ),
        ("Permissions",
          {"fields": ("is_staff", "is_active", "groups", "user_permissions")}
        ),
        ("Dates", 
         {"fields": ("last_login", "date_joined")}
        ),
    )

