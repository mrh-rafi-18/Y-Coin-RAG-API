import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from drf_spectacular_websocket.decorators import extend_ws_schema

from .models import Conversation, Message
from .serializers import (
    ChatCompletedSerializer,
    ChatErrorSerializer,
    ChatInputSerializer,
    ChatTokenSerializer,
)
from .services.instances import get_chat, get_retriever
from .services.query_processor import classify_user_intent, enhance_user_query

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        logger.info(f"WebSocket connection attempt by user: {user}")

        if not user or not user.is_authenticated:
            logger.warning("Unauthenticated connection rejected.")
            await self.close(code=4001)
            return

        await self.accept()
        logger.info("WebSocket connection accepted.")

    @extend_ws_schema(
        type="send",
        tags=["Websocket-Chat"],
        request=ChatInputSerializer,
        responses=ChatTokenSerializer
    )
    async def receive_json(self, content, **kwargs):
        # 1. Validate incoming message
        serializer = ChatInputSerializer(data=content)

        if not serializer.is_valid():
            await self.send_json({
                "type": "chat.error",
                "code": "invalid_input",
                "message": "Invalid input.",
                "details": serializer.errors,
            })
            return

        data = serializer.validated_data
        conversation_id = data.get("conversation_id")
        user_query = data["user_query"]
        user = self.scope["user"]

        # 2. Get existing conversation or create a new one
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user)

            if conversation is None:
                await self.send_json({
                    "type": "chat.error",
                    "code": "conversation_not_found",
                    "message": "Conversation not found or you do not have access to it.",
                })
                return
        else:
            conversation = await self.create_conversation(user)

        # 3. Save user's message
        user_message = await self.create_message(
            conversation=conversation,
            role=Message.Role.USER,
            content=user_query,
        )

        # Retrieve the current chat summary from the database (defaults to empty string if None)
        chat_summary = conversation.conversation_history_summary or ""
        system_prompt = "You are a helpful AI assistant for the Y-Coin crypto ecosystem."

        try:
            # 4. Initialize AI Orchestration
            chat_engine = get_chat()
            
            # Classify intent (blocking call wrapped in async)
            intent = await database_sync_to_async(classify_user_intent)(
                user_query=user_query, 
                chat_summary=chat_summary
            )

            # Determine which stream to use based on intent
            if intent.is_general_message:
                logger.info("Routing: Standard Chat")
                sync_response_stream = chat_engine.stream_standard_response(
                    system_message=system_prompt,
                    prev_chat_summary=chat_summary,
                    user_query=user_query
                )
            else:
                logger.info("Routing: RAG Chat")
                
                # Enhance query and retrieve documents safely in async wrappers
                enhanced = await database_sync_to_async(enhance_user_query)(
                    user_query=user_query, 
                    chat_summary=chat_summary
                )
                enhanced_list = [enhanced.enhanced_query_1, enhanced.enhanced_query_2]
                
                retriever = get_retriever()
                documents = await database_sync_to_async(retriever.retrieve)(
                    original_query=user_query, 
                    enhanced_queries=enhanced_list
                )
                
                context_str = "\n\n".join([doc.page_content for doc in documents]) if documents else "No relevant documents found."
                
                sync_response_stream = chat_engine.stream_rag_response(
                    system_message=system_prompt,
                    prev_chat_summary=chat_summary,
                    context=context_str,
                    user_query=user_query
                )

            # Create an empty placeholder message for the assistant in the DB to associate tokens with
            assistant_message = await self.create_message(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=""
            )

            # 5. Safely stream synchronous generator over async WebSocket
            full_response = ""
            stream_iterator = iter(sync_response_stream)

            # Helper function to get the next chunk synchronously
            def _get_next_chunk():
                try:
                    return next(stream_iterator)
                except StopIteration:
                    return None

            while True:
                # Fetch the next token without blocking the ASGI event loop
                chunk = await database_sync_to_async(_get_next_chunk)()
                
                if chunk is None:
                    break
                    
                full_response += chunk

                # Send chunk to frontend
                output = ChatTokenSerializer({
                    "type": "chat.token",
                    "conversation_id": str(conversation.id),
                    "message_id": str(assistant_message.id),
                    "content": chunk,
                })
                await self.send_json(output.data)

            # 6. Post-Processing: Save full message content to database
            await self.update_message_content(assistant_message, full_response)

            # 7. Post-Processing: Update and save the conversation summary
            new_summary = await database_sync_to_async(chat_engine.summarize_chat)(
                prev_chat_summary=chat_summary,
                current_query=user_query,
                current_response=full_response
            )
            await self.update_conversation_summary(conversation, new_summary)

            # 8. Send completion signal
            completed_output = ChatCompletedSerializer({
                "type": "chat.completed",
                "conversation_id": str(conversation.id),
                "message_id": str(assistant_message.id),
            })
            await self.send_json(completed_output.data)

        except Exception as e:
            logger.error(f"Error during AI streaming pipeline: {e}", exc_info=True)
            await self.send_json({
                "type": "chat.error",
                "code": "ai_pipeline_failure",
                "message": "Encountered an internal error while processing the AI response.",
            })

    # ==========================================
    # Database Helper Methods
    # ==========================================

    @database_sync_to_async
    def get_conversation(self, conversation_id, user):
        return Conversation.objects.filter(id=conversation_id, user=user).first()

    @database_sync_to_async
    def create_conversation(self, user):
        # Setting a default title; this can be updated dynamically later if needed
        return Conversation.objects.create(user=user, title="New Conversation")

    @database_sync_to_async
    def create_message(self, conversation, role, content):
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
        )

    @database_sync_to_async
    def update_message_content(self, message, full_content):
        """Updates the assistant's message in the database after streaming finishes."""
        message.content = full_content
        message.save(update_fields=["content"])

    @database_sync_to_async
    def update_conversation_summary(self, conversation, new_summary):
        """Saves the new AI-generated summary to the conversation model."""
        conversation.conversation_history_summary = new_summary
        conversation.save(update_fields=["conversation_history_summary", "updated_at"])

    async def disconnect(self, code):
        logger.info(f"WebSocket disconnected with code {code}")