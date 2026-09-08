from django.conf import settings
from django.db import models

class Localisation(models.Model):
    # Un utilisateur (enfant) n'a qu'une seule position récente
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='localisation'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Position de {self.user.username} ({self.latitude}, {self.longitude})"