import graphene
from graphene_django.types import DjangoObjectType
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Notification
from invitation.models import Invitation, InvitationStatus
from django.core.mail import send_mail
from django.conf import settings
import os

# 🌟 NOUVEAUX IMPORTS : Finie l'URL brute, place à LangChain
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

User = get_user_model()

# --- FONCTION REFAITE AVEC LANGCHAIN ---
def generer_conseils_ia(nom_user, emoji, commentaire):
    api_key = os.environ.get('GROQ_API_KEY', getattr(settings, 'GROQ_API_KEY', None))
    
    if not api_key:
        return "\n💡 Conseils de l'IA (Secours) :\nPrenez de ses nouvelles dans les prochaines 24h avec un message bienveillant."

    try:
        
        llm = ChatGroq(
            model="llama-3.1-8b-instant",  # Aligné sur ton modèle stable
            temperature=0.7,
            groq_api_key=api_key,
            timeout=10
        )
        output_parser = StrOutputParser()

        # Création du Template de Prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("user", (
                "L'utilisateur {nom_user} ressent l'émotion {emoji}. Il a dit : '{commentaire}'. "
                "Donne 3 conseils très courts et bienveillants à son superviseur pour l'accompagner face à cette humeur."
            ))
        ])

        # Assemblage de la chaîne
        chain = prompt_template | llm | output_parser

        # Exécution de la requête
        commentaire_propre = commentaire if commentaire else "rien de particulier"
        reponse_ia = chain.invoke({
            "nom_user": nom_user,
            "emoji": emoji,
            "commentaire": commentaire_propre
        })

        return f"\n💡 Conseils de l'IA (Groq) :\n{reponse_ia}"

    except Exception as e:
        # Si une erreur survient, elle s'affiche clairement dans la console de ton serveur
        print(f"❌ [ERREUR REQUÊTE GROQ NOTIFICATION] : {e}")
        return "\n💡 Conseils de l'IA (Secours) :\nAstuce de secours : Essayez de l'écouter activement."


# --- TYPES GRAPHQL ---
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")

class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification
        fields = ("id", "titre", "message", "est_lu", "cree_le", "emetteur")


# --- MUTATION ---
class EnregistrerHumeurMutation(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        emoji = graphene.String(required=True)
        est_triste = graphene.Boolean(required=True)
        commentaire = graphene.String()

    def mutate(root, info, emoji, est_triste, commentaire=""):
        user = info.context.user
        
        if user.is_anonymous:
            raise Exception("🔐 Action impossible : vous devez être connecté.")

        invitations = Invitation.objects.filter(
            status=InvitationStatus.ACCEPTED
        ).filter(
            Q(from_user=user) | Q(to_user=user)
        )
        
        # Appel de notre service LangChain si l'enfant est triste
        conseils_ia = ""
        if est_triste:
            conseils_ia = generer_conseils_ia(user.username, emoji, commentaire)

        for inv in invitations:
            superviseur_friend = inv.to_user if inv.from_user_id == user.id else inv.from_user
            
            if superviseur_friend.role == 'supervisor':
                if est_triste:
                    titre_alerte = "⚠️ Alerte baisse de moral"
                    message_notif = f"{user.username} se sent triste ({emoji}). Cliquez pour voir comment l'aider."
                    
                    message_email = f"Bonjour {superviseur_friend.username},\n\n"
                    message_email += f"{user.username} a indiqué se sentir triste/fatigué ({emoji}).\n"
                    if commentaire:
                        message_email += f"Son commentaire : '{commentaire}'\n\n"
                    message_email += conseils_ia
                    
                    # 1. Création de la notification en BDD
                    Notification.objects.create(
                        destinataire=superviseur_friend,
                        emetteur=user,
                        titre=titre_alerte,
                        message=message_notif
                    )
                    
                    # 2. Envoi de l'Email
                    if superviseur_friend.email:
                        try:
                            send_mail(
                                subject=titre_alerte,
                                message=message_email,
                                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lifesync.com'),
                                recipient_list=[superviseur_friend.email],
                                fail_silently=False,
                            )
                        except Exception as e:
                            print(f"Erreur d'envoi d'email: {e}")

                else:
                    Notification.objects.create(
                        destinataire=superviseur_friend,
                        emetteur=user,
                        titre="🎉 Bonne nouvelle !",
                        message=f"{user.username} a partagé sa super forme aujourd'hui ({emoji}) !"
                    )

        return EnregistrerHumeurMutation(
            success=True, 
            message="Humeur synchronisée et partagée avec succès."
        )


# --- QUERIES ---
class Query(graphene.ObjectType):
    mes_notifications = graphene.List(NotificationType)

    def resolve_mes_notifications(root, info):
        user = info.context.user
        if user.is_anonymous:
            return Notification.objects.none()
        return Notification.objects.filter(destinataire=user, est_lu=False)


class Mutation(graphene.ObjectType):
    enregistrer_humeur = EnregistrerHumeurMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)