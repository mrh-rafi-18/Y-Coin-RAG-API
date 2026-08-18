from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs


User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        token = self.get_token(scope)

        if token:
            scope["user"] = await self.get_user(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(
            scope,
            receive,
            send,
        )

    def get_token(self, scope):
        query_string = scope.get("query_string", b"").decode("utf-8")

        print("========== WEBSOCKET QUERY STRING ==========")
        print(query_string)
        print("============================================")

        query_params = parse_qs(query_string)

        token = query_params.get("token", [None])[0]

        print("TOKEN:", token)

        return token

    @database_sync_to_async
    def get_user(self, token):
        try:
            access_token = AccessToken(token)

            user_id = access_token["user_id"]

            return User.objects.get(
                id=user_id,
                is_active=True,
            )

        except (TokenError, User.DoesNotExist):
            return AnonymousUser()