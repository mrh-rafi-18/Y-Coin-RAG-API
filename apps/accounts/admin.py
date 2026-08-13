from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "profile_name",
        "is_email_verified",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_email_verified",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "email",
        "profile_name",
        "username",
    )

    ordering = ("-created_at",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Profile",
            {
                "fields": (
                    "profile_name",
                    "avatar",
                    "is_email_verified",
                    "deleted_at",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )