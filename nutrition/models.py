from django.db import models
from django.conf import settings

class ProfilNutritionnel(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_nutrition')
    poids = models.FloatField(help_text="Poids en kg")
    taille = models.FloatField(help_text="Taille en cm")
    fruits_legumes_favoris = models.TextField(help_text="Liste séparée par des virgules")
    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil nutritionnel de {self.user.username}"

    @property
    def imc(self):
        if self.taille > 0:
            return round(self.poids / ((self.taille / 100) ** 2), 1)
        return None