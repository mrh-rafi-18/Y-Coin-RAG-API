from django.db import models

class LegalDocument(models.Model):
    class DocumentType(models.TextChoices):
        TERMS = "terms", "Terms & Conditions"
        PRIVACY = "privacy", "Privacy Policy"

    # unique=True guarantees only ONE of each can ever exist
    document_type = models.CharField(max_length=20, choices=DocumentType.choices, unique=True)
    content = models.TextField(blank=True, default="Content goes here...")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_documents"

    def __str__(self):
        return self.get_document_type_display()