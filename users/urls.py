from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LoginAPIView, RegisterAPIView, UserSearchView
from users.views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

# Le routeur de DRF génère automatiquement les routes du CRUD sous /management/
router = DefaultRouter()
router.register(r'management', UserViewSet, basename='user-management')

urlpatterns = [
    # 1. URL d'inscription (Création publique) -> POST /api/users/register/
    path('register/', RegisterAPIView.as_view(), name='user-register'),
    
    # 2. URL de connexion (Authentification) -> POST /api/users/login/
    path('login/', LoginAPIView.as_view(), name='user-login'),
  
    
    # 3. URLs du CRUD (List, Detail, Update, Delete) -> /api/users/management/
    path('', include(router.urls)),
 
    # 4. URL de recherche d'utilisateurs -> GET /api/users/search/
    path('search/', UserSearchView.as_view(), name='users-search'),

    # JWT Token URLs
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]