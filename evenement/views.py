from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Evenement
from .serializers import EvenementSerializer

class EvenementViewSet(viewsets.ModelViewSet):
    serializer_class = EvenementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        """
        Système de double visibilité :
        - Si c'est un superviseur, il voit les événements qu'il a créés (created_by).
        - Si c'est un enfant/élève, il voit les événements qui lui sont assignés (user).
        """
        return Evenement.objects.filter(Q(created_by=user) | Q(user=user))

    def perform_create(self, serializer):
        # 1. On enregistre l'événement en base de données
        evenement = serializer.save(created_by=self.request.user)
        
        # 2. Déclenchement automatique de l'e-mail à l'enfant affecté
        try:
            destinataire_email = evenement.user.email
            subject = f"📅 Nouvelle planification : {evenement.titre}"
            
            # Formatage propre des dates pour le mail
            start_str = evenement.start_at.strftime('%d/%m/%Y à %H:%M')
            end_str = evenement.end_at.strftime('%d/%m/%Y à %H:%M')

            message = f"Bonjour {evenement.user.username},\n\n" \
                      f"Votre superviseur ({self.request.user.username}) a planifié une nouvelle tâche dans votre calendrier.\n\n" \
                      f"Détails de l'événement :\n" \
                      f"-----------------------------------------\n" \
                      f"🔹 Titre : {evenement.titre}\n" \
                      f"🔹 Description : {evenement.description or 'Aucune'}\n" \
                      f"🔹 Lieu : {evenement.lieu or 'Non spécifié'}\n" \
                      f"📅 Début : {start_str}\n" \
                      f"📅 Fin : {end_str}\n" \
                      f"-----------------------------------------\n\n" \
                      f"Connectez-vous sur votre application pour consulter votre planning complet.\n" \
                      f"Bon travail !"

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinataire_email],
                fail_silently=False, # Change à True en production si tu ne veux pas bloquer l'API en cas de souci SMTP
            )
            print(f"--- [MAIL] Notification envoyée avec succès à {destinataire_email} ---")
            
        except Exception as e:
            # Évite de faire planter la création de l'événement en base si la configuration SMTP a un raté
            print(f"--- [ERREUR MAIL] Impossible d'envoyer l'e-mail : {str(e)} ---")