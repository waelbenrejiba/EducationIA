from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# 1. Serializer pour le Login (Payload reçu)
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Identifiants invalides.")
            if not user.is_active:
                raise serializers.ValidationError("Ce compte est désactivé.")
        else:
            raise serializers.ValidationError("Doit inclure le nom d'utilisateur et le mot de passe.")

        data["user"] = user
        return data

# 2. Serializer pour le CRUD de l'Utilisateur
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'role': {'required': True}  # On force le choix du rôle à la création
        }

    def create(self, validated_data):
        # Permet de créer un utilisateur en hashant correctement son mot de passe
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        # Permet de mettre à jour l'utilisateur (et son mot de passe s'il est fourni)
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        print("======== LE SERIALIZER CUSTOM S'EXÉCUTE CORRETCEMENT ========")
        token = super().get_token(user)
        # Ajoutez ici les infos que vous voulez dans le token
        token['role'] = user.role  if user.role else None  # suppose que votre modèle User a un champ 'role'
        return token

