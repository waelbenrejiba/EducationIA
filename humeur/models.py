from django.db import models
from django.conf import settings
from django.utils import timezone

class RelationSuivi(models.Model):
    enfant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lien_superviseur", limit_choices_to={'role': 'user'})
    superviseur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enfants_geres", limit_choices_to={'role': 'supervisor'})

    def __str__(self):
        return f"Superviseur {self.superviseur.username} -> Enfant {self.enfant.username}"

class HumeurJournal(models.Model):
    enfant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="humeurs", limit_choices_to={'role': 'user'})
    date = models.DateField(default=timezone.now)
    emoji = models.CharField(max_length=10)
    est_triste = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('enfant', 'date')

class NotificationSuperviseur(models.Model):
    superviseur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications_recues", limit_choices_to={'role': 'supervisor'})
    enfant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alertes_declenchees")
    type_alerte = models.CharField(max_length=50, default="ALERTE_TRISTESSE")
    message_resume_ia = models.TextField()
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)