import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from notification.models import Notification
from notification.schema import NotificationType
from .models import HumeurJournal, NotificationSuperviseur, RelationSuivi

# ── TYPES GRAPHQL ─────────────────────────────────────────────────────────────
class HumeurJournalType(DjangoObjectType):
    class Meta:
        model = HumeurJournal
        fields = ("id", "date", "emoji", "est_triste", "commentaire")

class NotificationSuperviseurType(DjangoObjectType):
    titre    = graphene.String()
    message  = graphene.String()
    est_lu   = graphene.Boolean()

    class Meta:
        model = NotificationSuperviseur
        fields = ("id", "type_alerte", "message_resume_ia", "lu", "created_at", "enfant")

    def resolve_titre(self, info):   return self.type_alerte
    def resolve_message(self, info): return self.message_resume_ia
    def resolve_est_lu(self, info):  return self.lu


# ── HELPER EMAIL ──────────────────────────────────────────────────────────────
def _envoyer_email_alerte_tristesse(enfant, superviseur, derniers_jours):
    """
    Envoie un email HTML au superviseur quand l'enfant est triste 3 jours de suite.
    Utilise automatiquement EMAIL_HOST / EMAIL_HOST_PASSWORD du .env
    """
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from datetime import datetime

    if not superviseur.email:
        print(f"⚠️ Superviseur {superviseur.username} sans email — mail non envoyé.")
        return

    # Résumé des 3 jours pour le corps du mail
    lignes_historique = ""
    for i, h in enumerate(reversed(list(derniers_jours))):
        commentaire = h.commentaire or "Aucun commentaire"
        lignes_historique += f"<li><strong>Jour {i+1} ({h.date.strftime('%d/%m')})</strong> : {h.emoji} — {commentaire}</li>"

    sujet = f"🚨 Alerte Tristesse — {enfant.get_full_name() or enfant.username} ({enfant.username})"

    corps_html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto">
        <div style="background:#e74c3c;padding:20px;border-radius:8px 8px 0 0">
            <h2 style="color:white;margin:0">🚨 Alerte — 3 jours de tristesse consécutifs</h2>
        </div>
        <div style="background:#f9f9f9;padding:20px;border:1px solid #ddd;border-radius:0 0 8px 8px">
            <p><strong>Enfant concerné :</strong> {enfant.get_full_name() or enfant.username} (@{enfant.username})</p>
            <p><strong>Date de l'alerte :</strong> {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
            <hr>
            <h3>📅 Historique des 3 derniers jours :</h3>
            <ul style="line-height:1.8">{lignes_historique}</ul>
            <hr>
            <h3>💡 Recommandation :</h3>
            <p>
                L'enfant présente des signes de détresse émotionnelle répétés.<br>
                <strong>Merci de prendre contact avec lui dans les plus brefs délais.</strong>
            </p>
            <hr>
            <p style="color:#aaa;font-size:11px">
                Message automatique généré par la plateforme Newgen.<br>
                Vous recevez cet email car vous êtes le superviseur de {enfant.username}.
            </p>
        </div>
    </body></html>
    """

    corps_texte = (
        f"Alerte : {enfant.username} est triste depuis 3 jours consécutifs.\n"
        f"Merci de le contacter rapidement.\n\n"
        f"Historique :\n" +
        "\n".join([f"- {h.date.strftime('%d/%m')} : {h.emoji} {h.commentaire or ''}" for h in reversed(list(derniers_jours))])
    )

    try:
        email = EmailMultiAlternatives(
            subject=sujet,
            body=corps_texte,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[superviseur.email],
        )
        email.attach_alternative(corps_html, "text/html")
        email.send(fail_silently=False)
        print(f"✅ Email alerte tristesse envoyé à {superviseur.email}")
    except Exception as e:
        print(f"❌ Échec envoi email alerte tristesse : {str(e)}")


# ── MUTATION : ENREGISTRER L'HUMEUR ──────────────────────────────────────────
class EnregistrerHumeurMutation(graphene.Mutation):
    class Arguments:
        emoji       = graphene.String(required=True)
        est_triste  = graphene.Boolean(required=True)
        commentaire = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()
    humeur  = graphene.Field(HumeurJournalType)

    def mutate(self, info, emoji, est_triste, commentaire=""):
        user = info.context.user

        if not user.is_authenticated or getattr(user, 'role', None) != 'user':
            raise Exception("Accès refusé. Seuls les enfants connectés peuvent soumettre leur humeur.")

        # Sauvegarde ou mise à jour de l'humeur du jour
        humeur, created = HumeurJournal.objects.update_or_create(
            enfant=user,
            date=timezone.now().date(),
            defaults={
                "emoji":       emoji,
                "est_triste":  est_triste,
                "commentaire": commentaire
            }
        )

        # ── Analyse des 3 derniers jours ──────────────────────────────────
        derniers_jours = HumeurJournal.objects.filter(enfant=user).order_by('-date')[:3]

        if len(derniers_jours) == 3 and all(h.est_triste for h in derniers_jours):
            try:
                relation    = RelationSuivi.objects.get(enfant=user)
                superviseur = relation.superviseur

                deja_alerte = NotificationSuperviseur.objects.filter(
                    enfant=user,
                    created_at__date=timezone.now().date(),
                    type_alerte="ALERTE_TRISTESSE"
                ).exists()

                if not deja_alerte:
                    commentaires_ia = [
                        f"- J{i+1}: {h.commentaire or 'Pas de texte'}"
                        for i, h in enumerate(reversed(list(derniers_jours)))
                    ]
                    resume_ia = (
                        f"[MCP/Groq] {user.username} montre des signes de détresse répétés. "
                        f"Historique : {', '.join(commentaires_ia)}"
                    )

                    # 1. Notification interne dans la plateforme
                    NotificationSuperviseur.objects.create(
                        superviseur=superviseur,
                        enfant=user,
                        type_alerte="ALERTE_TRISTESSE",
                        message_resume_ia=resume_ia
                    )

                    # ✅ 2. Email automatique au superviseur
                    _envoyer_email_alerte_tristesse(user, superviseur, derniers_jours)

            except RelationSuivi.DoesNotExist:
                pass  # Pas de superviseur associé

        return EnregistrerHumeurMutation(
            success=True,
            message="Humeur synchronisée.",
            humeur=humeur
        )


class Mutation(graphene.ObjectType):
    enregistrer_humeur = EnregistrerHumeurMutation.Field()


# ── QUERIES ───────────────────────────────────────────────────────────────────
class Query(graphene.ObjectType):
    mes_humeurs                   = graphene.List(HumeurJournalType)
    mes_notifications             = graphene.List(NotificationType)
    mes_notifications_superviseur = graphene.List(NotificationSuperviseurType)

    def resolve_mes_humeurs(self, info):
        user = info.context.user
        if user.is_authenticated and getattr(user, 'role', None) == 'user':
            return HumeurJournal.objects.filter(enfant=user).order_by('-date')
        return []

    def resolve_mes_notifications(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Notification.objects.filter(destinataire=user)
        return []

    def resolve_mes_notifications_superviseur(self, info):
        user = info.context.user
        if user.is_authenticated and getattr(user, 'role', None) == 'supervisor':
            return NotificationSuperviseur.objects.filter(
                superviseur=user
            ).order_by('-created_at')
        return []