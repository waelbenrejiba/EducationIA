from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
except Exception:
    JWTAuthentication = None

User = get_user_model()


@database_sync_to_async
def get_user_for_token(token: str):
    if not JWTAuthentication:
        return AnonymousUser()

    jwt_auth = JWTAuthentication()
    try:
        validated = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated)
        return user
    except Exception:
        return AnonymousUser()


class JwtAuthMiddleware:
   
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = None
        if "token" in query and query["token"]:
            token = query["token"][0]

        scope["user"] = await get_user_for_token(token) if token else AnonymousUser()
        return await self.app(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)