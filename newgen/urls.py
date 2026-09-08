from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .schema import schema

# ✅ On garde AuthenticatedGraphQLView ici, dans le fichier principal
class AuthenticatedGraphQLView(GraphQLView):
    def dispatch(self, request, *args, **kwargs):
        try:
            authenticator = JWTAuthentication()
            auth_res = authenticator.authenticate(request)
            if auth_res:
                request.user, request.auth = auth_res
                print(f"Utilisateur : {request.user.username} | Rôle : {getattr(request.user, 'role', 'Aucun')}")
            else:
                print("⚠️ Aucun token JWT trouvé.")
        except Exception as e:
            print(f"❌ Erreur JWT : {str(e)}")
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),

    # ✅ Un seul endpoint GraphQL avec JWT + schema global
    path("api/graphql/", csrf_exempt(AuthenticatedGraphQLView.as_view(graphiql=True, schema=schema))),

    path('api/', include('evenement.urls')),
    path('api/', include('invitation.urls')),
    path('api/', include('notification.urls')),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("chat.urls")),
    path("api/", include("ia.urls")),
    path("api/",include("gps.urls")),
]