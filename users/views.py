from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, get_user_model
from .models import User
from .serializers import UserSerializer, LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

User = get_user_model()

# --- 1. API D'INSCRIPTION (PUBLIQUE) ---
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]  # Tout le monde peut créer un compte

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Utilisateur créé avec succès",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- 2. API DE CONNEXION (PUBLIQUE) ---
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Initialise la session Django
        login(request, user)
        
        return Response({
            "message": "Connexion réussie",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)


# --- 3. API CRUD DE GESTION (SÉCURISÉE) ---
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Il faut obligatoirement être connecté

    def get_queryset(self):
        """
        POURQUOI ON NE LAISSE PAS User.objects.all() ?
        On filtre la base de données selon le rôle de l'utilisateur connecté.
        """
        user = self.request.user

        # Sécurité : Si l'utilisateur n'est pas identifié (anonyme), on renvoie une liste vide
        if user.is_anonymous:
            return User.objects.none()

        # Si c'est un Admin ou un Superviseur, il a le droit de TOUT voir et TOUT gérer
        if user.role in [User.ROLE_ADMIN, User.ROLE_SUPERVISOR] or user.is_superuser:
            return User.objects.all()

        # Si c'est un simple utilisateur ('user'), il n'a le droit de voir et modifier QUE son propre compte !
        # S'il tente d'accéder à /api/users/management/, il ne verra que lui-même.
        return User.objects.filter(id=user.id)


# --- 4. API DE RECHERCHE D'UTILISATEURS (SÉCURISÉE) ---
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response([])

        qs = (
            User.objects.filter(username__icontains=q)
            .exclude(id=request.user.id)
            .order_by("username")[:20]
        )

        data = [{"id": str(u.id), "username": u.username, "email": u.email} for u in qs]
        return Response(data)
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, get_user_model
from .models import User
from .serializers import UserSerializer, LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

User = get_user_model()

# --- 1. API D'INSCRIPTION (PUBLIQUE) ---
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]  # Tout le monde peut créer un compte

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Utilisateur créé avec succès",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- 2. API DE CONNEXION (PUBLIQUE) ---
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Initialise la session Django
        login(request, user)
        
        return Response({
            "message": "Connexion réussie",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)


# --- 3. API CRUD DE GESTION (SÉCURISÉE) ---
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Il faut obligatoirement être connecté

    def get_queryset(self):
        """
        POURQUOI ON NE LAISSE PAS User.objects.all() ?
        On filtre la base de données selon le rôle de l'utilisateur connecté.
        """
        user = self.request.user

        # Sécurité : Si l'utilisateur n'est pas identifié (anonyme), on renvoie une liste vide
        if user.is_anonymous:
            return User.objects.none()

        # Si c'est un Admin ou un Superviseur, il a le droit de TOUT voir et TOUT gérer
        if user.role in [User.ROLE_ADMIN, User.ROLE_SUPERVISOR] or user.is_superuser:
            return User.objects.all()

        # Si c'est un simple utilisateur ('user'), il n'a le droit de voir et modifier QUE son propre compte !
        # S'il tente d'accéder à /api/users/management/, il ne verra que lui-même.
        return User.objects.filter(id=user.id)


# --- 4. API DE RECHERCHE D'UTILISATEURS (SÉCURISÉE) ---
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response([])

        qs = (
            User.objects.filter(username__icontains=q)
            .exclude(id=request.user.id)
            .order_by("username")[:20]
        )

        data = [{"id": str(u.id), "username": u.username, "email": u.email} for u in qs]
        return Response(data)


# --- 5. API DE CONNEXION JWT (PUBLIQUE) ---
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# --- 5. API DE CONNEXION JWT (PUBLIQUE) ---
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer