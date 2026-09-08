# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
   
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    emetteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alertes_envoyees")
    
    titre = models.CharField(max_length=150)
    message = models.TextField()
    est_lu = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cree_le'] # La plus récente en premier

    def __str__(self):
        return f"Alerte pour {self.destinataire.username} de la part de {self.emetteur.username}"