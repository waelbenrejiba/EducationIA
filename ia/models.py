from django.db import models
from django.conf import settings
from django.utils import timezone

class BilanSanteMensuel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bilans_sante')
    # On enregistre toujours le 1er jour du mois (ex: 2026-05-01) pour faciliter les comparaisons
    mois = models.DateField(default=timezone.now) 
    
    # Données du quiz
    score_sommeil = models.IntegerField()
    score_sport = models.IntegerField()
    niveau_stress = models.IntegerField()
    humeur = models.CharField(max_length=100)
    
    # Résultat de l'IA Groq
    conseils_psychologiques = models.TextField(blank=True, null=True)

    class Meta:
        # Un utilisateur ne peut avoir qu'un seul bilan par mois
        unique_together = ('user', 'mois') 
        ordering = ['-mois'] # Tri du plus récent au plus ancien

    def __str__(self):
        return f"Bilan {self.mois.strftime('%B %Y')} - {self.user.username}"