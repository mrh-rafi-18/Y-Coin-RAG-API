import logging
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import LegalDocument
from .serializers import LegalDocumentSerializer
from .permissions import IsAdminRole

logger = logging.getLogger(__name__)

# Helper function to keep our Swagger schema code DRY (Don't Repeat Yourself)
def get_document_schema(doc_name):
    return {
        "list": extend_schema(
            summary=f"List all {doc_name} versions",
            description=f"Retrieves a list of all {doc_name} versions. Can be filtered by active status.",
            tags=["Admin dashboard"],
            parameters=[
                OpenApiParameter(
                    name="is_active",
                    description="Filter by active status (true/false).",
                    required=False,
                    type=OpenApiTypes.BOOL,
                    location=OpenApiParameter.QUERY
                )
            ]
        ),
        "retrieve": extend_schema(
            summary=f"Retrieve a {doc_name}",
            description=f"Gets the details of a specific {doc_name} by its ID.",
            tags=["Admin dashboard"]
        ),
        "create": extend_schema(
            summary=f"Create a {doc_name}",
            description=f"Uploads a new version of {doc_name}. The document type is inferred automatically.",
            tags=["Admin dashboard"]
        ),
        "update": extend_schema(
            summary=f"Update a {doc_name}",
            description=f"Fully updates a {doc_name}.",
            tags=["Admin dashboard"]
        ),
        "partial_update": extend_schema(
            summary=f"Partially update a {doc_name}",
            description=f"Partially updates a {doc_name} (e.g., toggling is_active).",
            tags=["Admin dashboard"]
        ),
        "destroy": extend_schema(
            summary=f"Delete a {doc_name}",
            description=f"Permanently deletes a {doc_name}.",
            tags=["Admin dashboard"]
        )
    }


@extend_schema_view(**get_document_schema("Terms & Conditions"))
class TermsAndConditionsViewSet(viewsets.ModelViewSet):
    """
    ViewSet exclusively for Terms & Conditions.
    """
    serializer_class = LegalDocumentSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        try:
            # Force the queryset to only return Terms & Conditions
            queryset = LegalDocument.objects.filter(document_type=LegalDocument.DocumentType.TERMS)
            
            is_active_param = self.request.query_params.get('is_active')
            if is_active_param is not None:
                is_active = is_active_param.lower() == 'true'
                queryset = queryset.filter(is_active=is_active)
                
            return queryset
        except Exception as e:
            logger.error(f"Error fetching Terms for admin {self.request.user.id}: {e}", exc_info=True)
            return LegalDocument.objects.none()

    def perform_create(self, serializer):
        # Automatically inject the correct document type on save
        serializer.save(document_type=LegalDocument.DocumentType.TERMS)


@extend_schema_view(**get_document_schema("Privacy Policy"))
class PrivacyPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet exclusively for Privacy Policies.
    """
    serializer_class = LegalDocumentSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        try:
            # Force the queryset to only return Privacy Policies
            queryset = LegalDocument.objects.filter(document_type=LegalDocument.DocumentType.PRIVACY)
            
            is_active_param = self.request.query_params.get('is_active')
            if is_active_param is not None:
                is_active = is_active_param.lower() == 'true'
                queryset = queryset.filter(is_active=is_active)
                
            return queryset
        except Exception as e:
            logger.error(f"Error fetching Privacy Policy for admin {self.request.user.id}: {e}", exc_info=True)
            return LegalDocument.objects.none()

    def perform_create(self, serializer):
        # Automatically inject the correct document type on save
        serializer.save(document_type=LegalDocument.DocumentType.PRIVACY)