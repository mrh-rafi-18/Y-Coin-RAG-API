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


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        print("WebSocket user:", user)
        print("Authenticated:", user.is_authenticated)

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.accept()

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

        # 2. Get existing conversation or create a new one
        if conversation_id:
            conversation = await self.get_conversation(
                conversation_id,
                self.scope["user"],
            )

            if conversation is None:
                await self.send_json({
                    "type": "chat.error",
                    "code": "conversation_not_found",
                    "message": "Conversation not found or you do not have access to it.",
                })
                return
        else:
            conversation = await self.create_conversation(
                self.scope["user"],
            )

        # 3. Save user's message
        message = await self.create_message(
            conversation,
            Message.Role.USER,
            user_query,
        )

        # 4. AI streaming
        #
        # async for token in ai_stream:
        #
        #     output = ChatTokenSerializer({
        #         "type": "chat.token",
        #         "conversation_id": conversation.id,
        #         "message_id": message.id,
        #         "content": token,
        #     })
        #
        #     await self.send_json(output.data)

        # 5. When streaming is complete
        output = ChatCompletedSerializer({
            "type": "chat.completed",
            "conversation_id": conversation.id,
            "message_id": message.id,
        })

        await self.send_json(output.data)

    @database_sync_to_async
    def get_conversation(self, conversation_id, user):
        return Conversation.objects.filter(
            id=conversation_id,
            user=user,
        ).first()

    @database_sync_to_async
    def create_conversation(self, user):
        return Conversation.objects.create(user=user)

    @database_sync_to_async
    def create_message(self, conversation, role, content):
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
        )

    async def disconnect(self, code):
        pass