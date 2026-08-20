from rest_framework import generics
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import LegalDocument
from .serializers import LegalDocumentSerializer
from ..accounts.permissions import IsAdminRole

# --- CONSOLIDATED VIEWS (GET for Public, PUT for Admin) ---

@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Terms & Conditions",
        description="Public endpoint to read the singleton Terms & Conditions.",
        tags=["Admin dashboard"]
    ),
    put=extend_schema(
        summary="Update Terms & Conditions (Admin)",
        description="Overwrites the existing Terms & Conditions document. Restricted to Admins.",
        tags=["Admin dashboard"]
    )
)
class TermsView(generics.RetrieveUpdateAPIView):
    serializer_class = LegalDocumentSerializer
    http_method_names = ['get', 'put']

    def get_permissions(self):
        """
        Allow anyone to read (GET), but restrict updates (PUT) to Admins.
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminRole()]

    def get_object(self):
        obj, _ = LegalDocument.objects.get_or_create(document_type=LegalDocument.DocumentType.TERMS)
        return obj


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Privacy Policy",
        description="Public endpoint to read the singleton Privacy Policy.",
        tags=["Admin dashboard"]
    ),
    put=extend_schema(
        summary="Update Privacy Policy (Admin)",
        description="Overwrites the existing Privacy Policy document. Restricted to Admins.",
        tags=["Admin dashboard"]
    )
)
class PrivacyView(generics.RetrieveUpdateAPIView):
    serializer_class = LegalDocumentSerializer
    http_method_names = ['get', 'put']

    def get_permissions(self):
        """
        Allow anyone to read (GET), but restrict updates (PUT) to Admins.
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminRole()]

    def get_object(self):
        obj, _ = LegalDocument.objects.get_or_create(document_type=LegalDocument.DocumentType.PRIVACY)
        return obj