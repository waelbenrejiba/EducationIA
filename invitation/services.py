from django.db.models import Q
from .models import Invitation, InvitationStatus


def are_friends(user_id, other_user_id) -> bool:
    """
    Deux users sont amis s'il existe une invitation ACCEPTED
    dans un sens ou dans l'autre.
    """
    return Invitation.objects.filter(
        status=InvitationStatus.ACCEPTED
    ).filter(
        Q(from_user_id=user_id, to_user_id=other_user_id)
        | Q(from_user_id=other_user_id, to_user_id=user_id)
    ).exists()