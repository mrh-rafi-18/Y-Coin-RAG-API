from django.db import models
from django.db.models import Q, UniqueConstraint

class LegalDocument(models.Model):
    # 1. Use TextChoices for cleaner code and type hinting
    class DocumentType(models.TextChoices):
        TERMS = "terms", "Terms & Conditions"
        PRIVACY = "privacy", "Privacy Policy"

    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    version = models.CharField(max_length=20)
    content = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_documents"
        ordering = ["-created_at"]
        constraints = [
            # 2. Prevent duplicate versions of the same document type
            UniqueConstraint(
                fields=["document_type", "version"],
                name="unique_document_version"
            ),
            # 3. Database-level lock: Only ONE active document per type allowed
            UniqueConstraint(
                fields=["document_type"],
                condition=Q(is_active=True),
                name="unique_active_document_per_type"
            )
        ]

    def __str__(self):
        # Displays like: "Terms & Conditions - v1.0 (Active)"
        status = "Active" if self.is_active else "Inactive"
        return f"{self.get_document_type_display()} - v{self.version} ({status})"

    def save(self, *args, **kwargs):
        # 4. Graceful handling: If this document is set to active, automatically 
        # deactivate all other documents of the same type.
        if self.is_active:
            LegalDocument.objects.filter(
                document_type=self.document_type, 
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
            
        super().save(*args, **kwargs)
