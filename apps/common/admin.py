from django.contrib import admin
from .models import LegalDocument


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ("document_type", "updated_at", "created_at")
    list_filter = ("document_type",)
    search_fields = ("content",)
    readonly_fields = ("created_at", "updated_at")