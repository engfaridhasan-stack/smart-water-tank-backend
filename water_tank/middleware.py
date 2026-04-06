import json
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(token_key):
    try:
        # টোকেন ভেরিফাই করে ইউজার আইডি বের করা
        token = AccessToken(token_key)
        return User.objects.get(id=token['user_id'])
    except Exception:
        return AnonymousUser()

class JwtAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # URL থেকে টোকেন খুঁজে বের করা (ws://.../?token=your_token)
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = dict(qc.split("=") for qc in query_string.split("&") if "=" in qc)
        token_key = query_params.get("token")

        if token_key:
            # ইউজারকে স্কোপের মধ্যে সেট করা
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser()

        # পরবর্তী ধাপে পাঠানো
        return await self.app(scope, receive, send)