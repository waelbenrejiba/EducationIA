from rest_framework import serializers
from .models import BilanSanteMensuel

class BilanSanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BilanSanteMensuel
        fields = ['id', 'mois', 'score_sommeil', 'score_sport', 'niveau_stress', 'humeur', 'conseils_psychologiques']
        # 'mois' et 'conseils_psychologiques' sont calculés par le serveur, Angular n'a pas à les envoyer
        read_only_fields = ['id', 'mois', 'conseils_psychologiques']