from .models import User
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import *


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = ["id", "profile_name", "email", "password", "avatar", "role", "is_email_verified", "deleted_at", "created_at", "updated_at"]
        read_only_fields = ["id", "role", "is_email_verified", "deleted_at", "created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)

        user = User(**validated_data)

        if password:
            user.set_password(password)

        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        new_avatar = validated_data.get("avatar")

        old_avatar = instance.avatar

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if new_avatar and old_avatar and old_avatar != instance.avatar:
            old_avatar.delete(save=False)

        return instance



class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()



class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6,)



class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


