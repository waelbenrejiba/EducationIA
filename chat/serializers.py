from rest_framework import serializers
from .models import PrivateMessage

class PrivateMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_id = serializers.UUIDField(source="sender.id", read_only=True)
    message = serializers.CharField(source="content") # Pour correspondre au payload WebSocket

    class Meta:
        model = PrivateMessage
        fields = ["id", "message", "sender_id", "sender_username", "created_at"]