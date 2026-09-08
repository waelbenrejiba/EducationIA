from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Invitation, InvitationStatus

User = get_user_model()


class InvitationCreateSerializer(serializers.Serializer):
    to_user_id = serializers.UUIDField()

    def validate_to_user_id(self, value):
        request = self.context["request"]
        if str(request.user.id) == str(value):
            raise serializers.ValidationError("You can't invite yourself.")
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")
        return value


class InvitationSerializer(serializers.ModelSerializer):
    from_user_username = serializers.CharField(source="from_user.username", read_only=True)
    to_user_username = serializers.CharField(source="to_user.username", read_only=True)

    class Meta:
        model = Invitation
        fields = [
            "id",
            "from_user",
            "from_user_username",
            "to_user",
            "to_user_username",
            "status",
            "created_at",
            "responded_at",
        ]
        read_only_fields = ["id", "from_user", "status", "created_at", "responded_at"]