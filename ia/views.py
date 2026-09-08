from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from .models import BilanSanteMensuel
from .serializers import BilanSanteSerializer
from .ia_service import PsychologieAIService

class GenererConseilsPsyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Validation des données d'Angular avec le Serializer
        serializer = BilanSanteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Détermination du mois actuel (forcé au 1er jour du mois)
        debut_mois = datetime.now().date().replace(day=1)
        user = request.user

        # 3. 🔍 Recherche du mois PRÉCÉDENT en Base de données
        # On prend le dernier bilan enregistré qui n'est pas celui de ce mois-ci
        bilan_precedent = BilanSanteMensuel.objects.filter(user=user).exclude(mois=debut_mois).order_by('-mois').first()

        # 4. Préparation des scores actuels validés
        scores_actuels = serializer.validated_data

        # 5.  Appel au service IA avec les données actuelles et passées
        ai_service = PsychologieAIService()
        conseils_ia = ai_service.generer_conseils_evolutifs(actuel=scores_actuels, precedent=bilan_precedent)

        # 6. Sauvegarde ou mise à jour du bilan de ce mois-ci
        bilan, created = BilanSanteMensuel.objects.update_or_create(
            user=user,
            mois=debut_mois,
            defaults={
                'score_sommeil': scores_actuels['score_sommeil'],
                'score_sport': scores_actuels['score_sport'],
                'niveau_stress': scores_actuels['niveau_stress'],
                'humeur': scores_actuels['humeur'],
                'conseils_psychologiques': conseils_ia # On ajoute le texte généré par Groq
            }
        )

        # 7. On renvoie le bilan complet mis à jour à Angular
        return Response(BilanSanteSerializer(bilan).data, status=status.HTTP_200_OK)