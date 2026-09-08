from django.conf import settings
from django.db import models
from django.db.models import Q


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class Invitation(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_invitations",
    )
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(from_user=models.F("to_user")),
                name="invitation_no_self_invite",
            ),
            models.UniqueConstraint(
                fields=["from_user", "to_user"],
                name="invitation_unique_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["from_user", "to_user", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.from_user_id} -> {self.to_user_id} ({self.status})"
