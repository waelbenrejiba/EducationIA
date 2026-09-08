from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Localisation
from django.contrib.auth import get_user_model

# Importe ton modèle de relation (ajuste le chemin selon ton projet)
# depuis ton app humeur ou invitation
# from humeur.models import RelationSuivi 

User = get_user_model()

class UpdateLocationView(views.APIView):
    permission_classes = [IsAuthenticated]

    # 1. L'enfant envoie sa position
    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not latitude or not longitude:
            return Response({"error": "Données manquantes"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Met à jour ou crée la localisation de l'utilisateur connecté
        loc, created = Localisation.objects.update_or_create(
            user=request.user,
            defaults={'latitude': latitude, 'longitude': longitude}
        )
        return Response({"message": "Position mise à jour"}, status=status.HTTP_200_OK)


class SupervisorEnfantsLocationView(views.APIView):
    permission_classes = [IsAuthenticated]

    # 2. Le superviseur récupère la carte de SES enfants
    def get(self, request):
        user = request.user
        if user.role != 'supervisor':
            return Response({"detail": "Accès interdit"}, status=status.HTTP_403_FORBIDDEN)
        
        # Pour le test, on prend tous les rôles 'user' qui ont une localisation :
        enfants_localisations = Localisation.objects.filter(user__role='user').select_related('user')
        
        data = []
        for loc in enfants_localisations:
            data.append({
                "username": loc.user.username,
                "email": loc.user.email,
                "latitude": float(loc.latitude),
                "longitude": float(loc.longitude),
                "updated_at": loc.updated_at
            })
            
        return Response(data, status=status.HTTP_200_OK)