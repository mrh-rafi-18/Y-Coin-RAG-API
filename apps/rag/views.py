import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

logger = logging.getLogger(__name__)

@extend_schema_view(
    list=extend_schema(
        summary="List all conversations",
        description="Retrieves a list of all conversations owned by the authenticated user, ordered by the last message time.",
        tags=["Conversations"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a conversation",
        description="Gets the details of a specific conversation by its UUID.",
        tags=["Conversations"]
    ),
    update=extend_schema(
        summary="Update a conversation",
        description="Fully updates a conversation (e.g., modifying the title).",
        tags=["Conversations"]
    ),
    partial_update=extend_schema(
        summary="Partially update a conversation",
        description="Partially updates a conversation (e.g., renaming the title via PATCH).",
        tags=["Conversations"]
    ),
    destroy=extend_schema(
        summary="Delete a conversation",
        description="Permanently deletes a conversation and all its associated messages.",
        tags=["Conversations"]
    )
)
class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing user conversations.
    Creation (POST) is explicitly disabled as it is handled by the WebSocket consumer.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Strictly isolate data: Users can only see and interact with their own conversations.
        """
        try:
            return Conversation.objects.filter(user=self.request.user)
        except Exception as e:
            logger.error(f"Error fetching conversations for user {self.request.user.id}: {e}", exc_info=True)
            return Conversation.objects.none()


@extend_schema_view(
    list=extend_schema(
        summary="List messages for a conversation",
        description="Retrieves all messages associated with a specific conversation_id, ordered chronologically.",
        tags=["Messages"],
        parameters=[
            OpenApiParameter(
                name="conversation_id",
                description="The UUID of the conversation to fetch messages for.",
                required=True,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY
            )
        ]
    )
)
class MessageViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for retrieving messages.
    Creation, updating, and deletion are disabled to maintain chat integrity.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves messages associated with a specific conversation_id passed in the query parameters.
        Ensures the requesting user actually owns the parent conversation.
        """
        conversation_id = self.request.query_params.get('conversation_id')

        if not conversation_id:
            logger.warning(f"User {self.request.user.id} requested messages without providing a conversation_id.")
            raise ValidationError({"conversation_id": "This query parameter is required."})

        try:
            # The queryset spans the relationship to ensure the user owns the parent conversation
            return Message.objects.filter(
                conversation_id=conversation_id,
                conversation__user=self.request.user
            )
            
        except DjangoValidationError:
            # Catches improperly formatted UUIDs passed in the URL
            raise ValidationError({"conversation_id": "Must be a valid UUID."})
        except Exception as e:
            logger.error(f"Error fetching messages for conversation {conversation_id}: {e}", exc_info=True)
            return Message.objects.none()