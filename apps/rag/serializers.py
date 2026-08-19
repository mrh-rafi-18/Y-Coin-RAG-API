from rest_framework import serializers
from .models import Conversation, Message

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'user', 'title', 'conversation_history_summary', 'last_message_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'last_message_at','conversation_history_summary', 'created_at', 'updated_at']



class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']



class ChatInputSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["chat.message"])
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    user_query = serializers.CharField(min_length=1, max_length=10000)



class ChatTokenSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["chat.token"])
    conversation_id = serializers.UUIDField()
    message_id = serializers.UUIDField()
    content = serializers.CharField()


class ChatCompletedSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["chat.completed"])
    conversation_id = serializers.UUIDField()
    message_id = serializers.UUIDField()


class ChatErrorSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["chat.error"])
    code = serializers.CharField()
    message = serializers.CharField()