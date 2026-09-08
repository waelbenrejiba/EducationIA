from rest_framework import permissions
from django.db.models import Q
from .models import Invitation, InvitationStatus

def are_friends(user1_id, user2_id):
    return Invitation.objects.filter(
        status=InvitationStatus.ACCEPTED
    ).filter(
        Q(from_user_id=user1_id, to_user_id=user2_id) | 
        Q(from_user_id=user2_id, to_user_id=user1_id)
    ).exists()

class IsSupervisorOrSelf(permissions.BasePermission):
    """
    Autorise l'accès si l'utilisateur demande ses propres données 
    ou celles d'un utilisateur avec qui il a une invitation acceptée.
    """
    def has_permission(self, request, view):
        # On suppose que l'ID de l'utilisateur ciblé est passé dans l'URL (ex: /api/evenements/<target_user_id>/)
        # ou en paramètre GET (ex: /api/evenements/?user_id=...)
        target_user_id = view.kwargs.get('user_id') or request.query_params.get('user_id')
        
        if not target_user_id:
            # S'il n'y a pas d'ID spécifié, on l'autorise (il verra ses propres données via request.user)
            return True
            
        if str(request.user.id) == str(target_user_id):
            return True
            
        return are_friends(request.user.id, target_user_id)