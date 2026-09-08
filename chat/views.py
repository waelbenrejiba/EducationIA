from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PrivateRoom, PrivateMessage
from .serializers import PrivateMessageSerializer

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, other_user_id):
        # Recréer la même clé stable que dans le WebSocket
        u1, u2 = (request.user.id, other_user_id) if str(request.user.id) < str(other_user_id) else (other_user_id, request.user.id)
        key = f"{u1}:{u2}"

        room = PrivateRoom.objects.filter(key=key).first()
        if not room:
            return Response([])  # Aucune salle/message pour l'instant

        messages = PrivateMessage.objects.filter(room=room).order_by("created_at")
        serializer = PrivateMessageSerializer(messages, many=True)
        return Response(serializer.data)

