import json
from uuid import UUID

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import PrivateRoom, PrivateMessage

User = get_user_model()


def _room_group_name(room_id: int) -> str:
    return f"private_room_{room_id}"


def _make_key(user_id, other_user_id) -> str:
    a, b = str(user_id), str(other_user_id)
    return f"{a}:{b}" if a < b else f"{b}:{a}"


class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(code=4401)  # Unauthorized
            return

        other_user_id = self.scope["url_route"]["kwargs"]["other_user_id"]
        try:
            other_uuid = UUID(other_user_id)
        except Exception:
            await self.close(code=4400)  # Bad request
            return

        room = await self._get_or_create_private_room(user.id, other_uuid)
        if room is None:
            await self.close(code=4404)
            return

        self.room_id = room.id
        self.group_name = _room_group_name(self.room_id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        user = self.scope["user"]
        payload = json.loads(text_data or "{}")

        content = (payload.get("message") or "").strip()
        if not content:
            return

        msg = await self._create_message(self.room_id, user.id, content)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "private.message",
                "id": msg["id"],
                "message": msg["content"],
                "sender_id": str(msg["sender_id"]),
                "sender_username": msg["sender_username"],
                "created_at": msg["created_at"],
                "room_id": self.room_id,
            },
        )

    async def private_message(self, event):
        await self.send(text_data=json.dumps(event))

    # ---------- DB helpers ----------
    @database_sync_to_async
    def _get_or_create_private_room(self, user1_id, user2_id):
        # Vérifier que l'autre user existe
        if not User.objects.filter(id=user2_id).exists():
            return None

        key = _make_key(user1_id, user2_id)

        # Normaliser user1/user2 selon l'ordre du key
        u1, u2 = (user1_id, user2_id) if str(user1_id) < str(user2_id) else (user2_id, user1_id)

        room, _ = PrivateRoom.objects.get_or_create(
            key=key,
            defaults={"user1_id": u1, "user2_id": u2},
        )
        return room

    @database_sync_to_async
    def _create_message(self, room_id: int, sender_id, content: str):
        room = PrivateRoom.objects.get(id=room_id)
        sender = User.objects.get(id=sender_id)
        m = PrivateMessage.objects.create(room=room, sender=sender, content=content)
        return {
            "id": m.id,
            "content": m.content,
            "sender_id": sender.id,
            "sender_username": sender.username,
            "created_at": m.created_at.isoformat(),
        }