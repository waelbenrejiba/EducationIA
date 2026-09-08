from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication 

class AuthenticatedGraphQLView(GraphQLView):
    def dispatch(self, request, *args, **kwargs):
        try:
            authenticator = JWTAuthentication()
            auth_res = authenticator.authenticate(request)
            if auth_res:
                request.user, request.auth = auth_res
                print(f"=== [GraphQL Auth Validation] ===")
                print(f"Utilisateur trouvé : {request.user.username}")
                print(f"Rôle de l'utilisateur : {getattr(request.user, 'role', 'Aucun rôle')}")
            else:
                print("⚠️ [GraphQL Auth] Aucun jeton Authorization trouvé dans les headers.")
        except Exception as e:
          
            print(f" [GraphQL Auth Error] Échec du décodage du jeton : {str(e)}")
        
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
]