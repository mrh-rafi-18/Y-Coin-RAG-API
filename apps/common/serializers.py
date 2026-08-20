from rest_framework import serializers
from .models import LegalDocument

class LegalDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(
        source="get_document_type_display",
        read_only=True,
    )

    class Meta:
        model = LegalDocument
        fields = ["id", "document_type", "document_type_display", "content", "updated_at"]
        read_only_fields = ["id", "document_type", "document_type_display", "updated_at"]