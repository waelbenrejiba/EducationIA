from rest_framework import serializers
from .models import Evenement
from django.contrib.auth import get_user_model

User = get_user_model()

class EvenementSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    user_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Evenement
        fields = [
            'id', 'titre', 'description', 'lieu', 
            'start_at', 'end_at', 'user_id', 'created_by', 'user_details'
        ]
      
        read_only_fields = ['created_by']

    def get_user_details(self, obj):
        return {
            "id": str(obj.user.id),
            "username": obj.user.username,
            "role": obj.user.role
        }
