from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
import uuid
from django.core.validators import RegexValidator
class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # On force le rôle à 'admin' pour les superusers
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)
class User(AbstractUser):
    # 1. On définit les rôles possibles
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROLE_USER = 'user'
    ROLE_SUPERVISOR = 'supervisor'
    ROLE_ADMIN = 'admin'
    phone_validator = RegexValidator(
        regex=r'^\+216\d{8}$',
        message="Le numéro de téléphone doit être au format tunisien : '+216' suivi de 8 chiffres (ex: +21620123456)."
    )
    
    # On applique le validateur au champ tel
    tel = models.CharField(
        max_length=12,  # +216 (4 caractères) + 8 chiffres = 12 caractères max
        validators=[phone_validator], 
        blank=True, 
        null=True
    )
    ville=models.CharField(max_length=100, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    ROLE_CHOICES = [
        ('user', 'Utilisateur Standard'),
        ('supervisor', 'Superviseur'),
        ('admin', 'Administrateur'),
    ]
    
    # 2. On ajoute le champ rôle à la base de données
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER, # Par défaut, un nouvel inscrit est un simple 'user'
    )

    # 3. Des propriétés pratiques pour vérifier les rôles dans tes vues ou templates
    @property
    def is_supervisor(self):
        return self.role == self.ROLE_SUPERVISOR

    @property
    def is_regular_user(self):
        return self.role == self.ROLE_USER