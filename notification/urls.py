# urls.py
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .schema import schema # 👈 Importe le schéma global que l'on vient de nettoyer

class AuthenticatedGraphQLView(GraphQLView):
    def dispatch(self, request, *args, **kwargs):
        # 1. On intercepte la requête pour lire le Token JWT
        authenticator = JWTAuthentication()
        try:
            auth_result = authenticator.authenticate(request)
            if auth_result is not None:
                user, token = auth_result
                request.user = user  # 2. On attache l'utilisateur connecté à la requête
        except Exception:
            pass # Si le token est invalide, on laisse AnonymousUser

        # 3. On passe la requête à GraphQL
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 🎯 L'unique point d'entrée pour ton application Angular
    # Utiliser csrf_exempt + AuthenticatedGraphQLView
    path('graphql/', csrf_exempt(AuthenticatedGraphQLView.as_view(graphiql=True, schema=schema))),
]