"""
tools.py — mcp_engine
Fonctions Django pures appelables par schema.py et mcp_server.py
"""

from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()



def extraire_historique_emojis_enfant(username_enfant: str) -> str:
    from notification.models import Notification

    alertes = Notification.objects.filter(
        emetteur__username=username_enfant
    ).order_by("-cree_le")[:5]

    if not alertes.exists():
        return f"Aucun historique d'émojis pour '{username_enfant}'. Première interaction."

    historique = ""
    for a in alertes:
        date_str = a.cree_le.strftime("%d/%m %H:%M")
        historique += f"- [{date_str}] {a.titre} : {a.message}\n"

    return historique



def analyser_humeur_semaine(username_enfant: str) -> str:
    from humeur.models import HumeurJournal  

    try:
        user   = User.objects.get(username=username_enfant)
        depuis = datetime.now() - timedelta(days=7)

        humeurs = HumeurJournal.objects.filter(
            enfant=user,
            date__gte=depuis.date()        # date (DateField) pas DateTimeField
        ).order_by("-date")

        if not humeurs.exists():
            return f"Aucune donnée d'humeur cette semaine pour '{username_enfant}'."

        nb_triste = 0
        rapport   = f"Humeur sur 7 jours — {username_enfant} :\n"
        for h in humeurs:
            etat = "⚠️ TRISTE/FATIGUÉ" if h.est_triste else "✅ Stable"
            if h.est_triste:
                nb_triste += 1
            rapport += (
                f"- [{h.date.strftime('%d/%m')}] "
                f"Émoji: {h.emoji} | État: {etat} | "
                f"Commentaire: '{h.commentaire or 'aucun'}'\n"
            )

        rapport += f"\nRésumé : {nb_triste}/{humeurs.count()} entrées négatives cette semaine."
        return rapport

    except Exception as e:
        return f"Erreur analyse humeur : {str(e)}"



def evaluer_niveau_risque(username_enfant: str) -> str:
    from notification.models import Notification
    from humeur.models import HumeurJournal  

    try:
        user       = User.objects.get(username=username_enfant)
        depuis_48h = datetime.now() - timedelta(hours=48)
        depuis_7j  = datetime.now() - timedelta(days=7)

        alertes_recentes = Notification.objects.filter(
            emetteur=user,
            cree_le__gte=depuis_48h
        ).count()

        episodes_tristes = HumeurJournal.objects.filter(
            enfant=user,
            est_triste=True,
            date__gte=depuis_7j.date()     # DateField
        ).count()

        score = (alertes_recentes * 2) + episodes_tristes

        if score == 0:
            niveau, detail = "FAIBLE",   "Aucune alerte récente, humeur stable."
        elif score <= 2:
            niveau, detail = "MODÉRÉ",   "Quelques signaux à surveiller."
        elif score <= 5:
            niveau, detail = "ÉLEVÉ",    "Plusieurs alertes. Intervention recommandée."
        else:
            niveau, detail = "CRITIQUE", "Situation préoccupante. Alerte immédiate nécessaire."

        return (
            f"Niveau de risque : {niveau}\n"
            f"Score           : {score}\n"
            f"Alertes (48h)   : {alertes_recentes}\n"
            f"Tristesse (7j)  : {episodes_tristes}\n"
            f"Analyse         : {detail}"
        )

    except Exception as e:
        return f"Erreur évaluation risque : {str(e)}"



def envoyer_alerte_email_superviseur(
    username_enfant: str,
    niveau_risque: str,
    analyse_ia: str
) -> str:
    from humeur.models import RelationSuivi  

    try:
        enfant = User.objects.get(username=username_enfant)

        # Récupère les superviseurs via RelationSuivi
        relations   = RelationSuivi.objects.filter(enfant=enfant).select_related("superviseur")
        superviseurs = [r.superviseur for r in relations if r.superviseur.email and r.superviseur.email.strip()]

        print(f"DEBUG relations: {relations.count()}")
        for r in relations:
            print(f"DEBUG superviseur: {r.superviseur.username} | email: {repr(r.superviseur.email)}")

        if not superviseurs:
            return "⚠️ Aucun superviseur avec email trouvé. Email non envoyé."

        sujet = f"🚨 Alerte {niveau_risque} — {enfant.get_full_name() or enfant.username}"

        corps_html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto">
            <div style="background:#e74c3c;padding:20px;border-radius:8px 8px 0 0">
                <h2 style="color:white;margin:0">🚨 Alerte Émotionnelle — Niveau {niveau_risque}</h2>
            </div>
            <div style="background:#f9f9f9;padding:20px;border:1px solid #ddd">
                <p><strong>Enfant :</strong> {enfant.get_full_name() or enfant.username} (@{username_enfant})</p>
                <p><strong>Date :</strong> {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
                <hr>
                <h3>📊 Analyse de l'IA :</h3>
                <div style="background:#fff;padding:15px;border-left:4px solid #e74c3c;
                            border-radius:4px;white-space:pre-wrap">{analyse_ia}</div>
                <hr>
                <p style="color:#888;font-size:12px">
                    Message automatique — Plateforme Newgen.<br>
                    Merci de contacter l'enfant dans les plus brefs délais.
                </p>
            </div>
        </body></html>
        """

        corps_texte  = f"Alerte {niveau_risque} pour {enfant.username}.\n\n{analyse_ia}"
        destinataires = [s.email for s in superviseurs]

        email = EmailMultiAlternatives(
            subject=sujet,
            body=corps_texte,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinataires,
        )
        email.attach_alternative(corps_html, "text/html")
        email.send(fail_silently=False)

        return f"✅ Email envoyé à {len(destinataires)} superviseur(s) : {', '.join(destinataires)}"

    except Exception as e:
        return f"❌ Échec envoi email : {str(e)}"



def creer_notification_interne(
    username_enfant: str,
    titre: str,
    message: str
) -> str:
    from humeur.models import RelationSuivi
    from notification.models import Notification

    try:
        enfant    = User.objects.get(username=username_enfant)
        relations = RelationSuivi.objects.filter(enfant=enfant).select_related("superviseur")

        if not relations.exists():
            return "⚠️ Aucun superviseur trouvé pour créer la notification interne."

        nb = 0
        for relation in relations:
            # ✅ destinataire = superviseur, emetteur = enfant
            Notification.objects.create(
                destinataire=relation.superviseur,
                emetteur=enfant,
                titre=f"[IA] {titre}",
                message=message,
            )
            nb += 1

        return f"✅ {nb} notification(s) interne(s) créée(s) pour '{username_enfant}'."

    except Exception as e:
        return f"❌ Erreur création notification : {str(e)}"



def get_profil_nutritionnel(username_enfant: str) -> str:
    try:
        from nutrition.models import ProfilNutritionnel
        user   = User.objects.get(username=username_enfant)
        profil = ProfilNutritionnel.objects.get(utilisateur=user)
        return (
            f"Profil nutritionnel de '{username_enfant}' :\n"
            f"- Allergies  : {profil.allergies or 'aucune'}\n"
            f"- Régime     : {profil.regime_alimentaire or 'standard'}\n"
            f"- Préférences: {profil.preferences or 'non renseignées'}\n"
        )
    except Exception as e:
        return f"Profil nutritionnel non trouvé : {str(e)}"
