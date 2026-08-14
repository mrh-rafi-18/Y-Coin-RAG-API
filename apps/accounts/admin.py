from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, OTP



@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "profile_name",
        "role",
        "is_email_verified",
        "is_staff",
        "is_superuser",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_email_verified",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = (
        "email",
        "profile_name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (None, {
            "fields": ("email", "password")
        }),
        ("Personal Information", {
            "fields": ("profile_name", "avatar")
        }),
        ("Role & Verification", {
            "fields": (
                "role",
                "is_email_verified",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
                "created_at",
                "updated_at",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "profile_name",
                "password1",
                "password2",
            ),
        }),
    )



@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "purpose",
        "expires_at",
        "is_used",
        "created_at",
    )
    list_filter = (
        "purpose",
        "is_used",
        "created_at",
    )
    search_fields = ("email",)
    readonly_fields = (
        "id",
        "created_at",
    )
    ordering = ("-created_at",)