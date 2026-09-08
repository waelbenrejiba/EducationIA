from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from invitation.permissions import IsSupervisorOrSelf

from .models import Invitation, InvitationStatus
from .serializers import InvitationSerializer, InvitationCreateSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class InvitationSendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = InvitationCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        to_user_id = ser.validated_data["to_user_id"]

        # Empêche doublons
        inv, created = Invitation.objects.get_or_create(
            from_user=request.user,
            to_user_id=to_user_id,
            defaults={"status": InvitationStatus.PENDING},
        )

        if not created and inv.status == InvitationStatus.ACCEPTED:
            return Response({"detail": "Already friends."}, status=status.HTTP_400_BAD_REQUEST)

        if not created and inv.status == InvitationStatus.PENDING:
            return Response({"detail": "Invitation already sent."}, status=status.HTTP_400_BAD_REQUEST)

        # Si rejetée avant, on la remet pending (optionnel)
        inv.status = InvitationStatus.PENDING
        inv.responded_at = None
        inv.save(update_fields=["status", "responded_at"])

        return Response(InvitationSerializer(inv).data, status=status.HTTP_201_CREATED)


class InvitationInboxView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        received = Invitation.objects.filter(to_user=request.user).order_by("-created_at")
        sent = Invitation.objects.filter(from_user=request.user).order_by("-created_at")
        return Response(
            {
                "received": InvitationSerializer(received, many=True).data,
                "sent": InvitationSerializer(sent, many=True).data,
            }
        )


class InvitationRespondView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invitation_id: int, action: str):
        try:
            inv = Invitation.objects.get(id=invitation_id, to_user=request.user)
        except Invitation.DoesNotExist:
            return Response({"detail": "Invitation not found."}, status=status.HTTP_404_NOT_FOUND)

        if inv.status != InvitationStatus.PENDING:
            return Response({"detail": "Invitation already processed."}, status=status.HTTP_400_BAD_REQUEST)

        if action == "accept":
            inv.status = InvitationStatus.ACCEPTED
        elif action == "reject":
            inv.status = InvitationStatus.REJECTED
        else:
            return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        inv.responded_at = timezone.now()
        inv.save(update_fields=["status", "responded_at"])
        return Response(InvitationSerializer(inv).data)


class FriendsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Cherche toutes les invitations acceptées où l'utilisateur est impliqué
        invitations = Invitation.objects.filter(
            status=InvitationStatus.ACCEPTED
        ).filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        )

        # Récupère les amis (l'autre utilisateur de chaque invitation)
        friend_ids = set()
        for inv in invitations:
            if inv.from_user_id == request.user.id:
                friend_ids.add(inv.to_user_id)
            else:
                friend_ids.add(inv.from_user_id)

        # Filtre uniquement ceux qui sont superviseurs
        friends = User.objects.filter(id__in=friend_ids)

        data = [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "role": u.role, # Renvoie 'user' ou 'supervisor'
            }
            for u in friends
        ]
        return Response(data, status=status.HTTP_200_OK)


class UserDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSupervisorOrSelf]

    def get(self, request):
        # Logique pour le tableau de bord de l'utilisateur
        pass
