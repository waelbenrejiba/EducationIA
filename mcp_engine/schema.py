"""
schema.py — mcp_engine
GraphQL Query : analyse autonome de l'enfant avec LangChain + outils MCP
"""

import os
import json
import graphene
from django.conf import settings
from django.contrib.auth import get_user_model

from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .tools import (
    extraire_historique_emojis_enfant,
    analyser_humeur_semaine,
    evaluer_niveau_risque,
    envoyer_alerte_email_superviseur,
    creer_notification_interne,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# TYPES GRAPHQL
# ─────────────────────────────────────────────────────────────────────────────
class CoachingParentType(graphene.ObjectType):
    conseil_parental = graphene.String()
    analyse_rythme   = graphene.String()


class AnalyseComportementsType(graphene.ObjectType):
    niveau_risque        = graphene.String()
    analyse_complete     = graphene.String()
    email_envoye         = graphene.Boolean()
    notification_creee   = graphene.Boolean()
    message_statut       = graphene.String()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS PRIVÉS
# ─────────────────────────────────────────────────────────────────────────────
def _get_llm():
    """Instancie le LLM Groq depuis les settings."""
    api_key = os.environ.get("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", None))
    if not api_key:
        raise ValueError("GROQ_API_KEY manquante dans les variables d'environnement.")
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.4,
        groq_api_key=api_key,
        timeout=30,
    )


def _extraire_niveau_depuis_texte(texte_risque: str) -> str:
    """Extrait le niveau FAIBLE/MODÉRÉ/ÉLEVÉ/CRITIQUE depuis le texte retourné."""
    for niveau in ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE"]:
        if niveau in texte_risque.upper():
            return niveau
    return "INCONNU"


# ─────────────────────────────────────────────────────────────────────────────
# QUERY GRAPHQL
# ─────────────────────────────────────────────────────────────────────────────
class Query(graphene.ObjectType):

    # ── Query 1 : Coaching parental (existante, conservée) ───────────────────
    obtenir_aide_parentale = graphene.Field(
        CoachingParentType,
        username_enfant=graphene.String(required=True)
    )

    # ── Query 2 : Analyse autonome complète avec email auto ──────────────────
    analyser_enfant_complet = graphene.Field(
        AnalyseComportementsType,
        username_enfant=graphene.String(required=True)
    )

    # ─────────────────────────────────────────────────────────────────────────
    def resolve_obtenir_aide_parentale(root, info, username_enfant):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Accès réservé aux utilisateurs connectés.")

        try:
            target_user = User.objects.get(username=username_enfant)
        except User.DoesNotExist:
            raise Exception(f"L'enfant '{username_enfant}' est introuvable.")

        # Extraction du contexte via outil MCP
        contexte_emojis = extraire_historique_emojis_enfant(target_user.username)

        try:
            llm = _get_llm()

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", (
                    "Tu es un pédopsychologue expert. Un enfant utilise notre application "
                    "pour communiquer ses émotions via des émojis car il n'arrive pas à parler "
                    "lorsqu'il est triste. Son parent reçoit une alerte. "
                    "En te basant sur l'historique des émojis, donne au parent des conseils "
                    "très concrets : quelle posture physique adopter, quel premier mot dire "
                    "pour le rassurer sans le forcer à parler."
                )),
                ("user", "Voici l'historique d'émojis de l'enfant :\n{contexte}")
            ])

            chain = prompt_template | llm | StrOutputParser()
            reponse_ia = chain.invoke({"contexte": contexte_emojis})

            return CoachingParentType(
                conseil_parental=reponse_ia,
                analyse_rythme="Analyse comportementale basée sur les émojis (LangChain + MCP)"
            )

        except Exception as e:
            print(f"❌ [ERREUR LANGCHAIN MCP ENGINE] : {e}")
            return CoachingParentType(
                conseil_parental=f"Erreur détaillée : {str(e)}",
                analyse_rythme="Erreur Moteur LangChain"
            )

    # ─────────────────────────────────────────────────────────────────────────
    def resolve_analyser_enfant_complet(root, info, username_enfant):
        """
        Analyse AUTONOME complète :
        1. Récupère historique émojis
        2. Analyse humeur semaine
        3. Évalue niveau de risque
        4. Si ÉLEVÉ/CRITIQUE → envoie email auto + notif interne
        5. Génère analyse IA complète
        """
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Accès réservé aux utilisateurs connectés.")

        try:
            User.objects.get(username=username_enfant)
        except User.DoesNotExist:
            raise Exception(f"L'enfant '{username_enfant}' est introuvable.")

        email_envoye       = False
        notification_creee = False
        messages_statut    = []

        try:
            # ── ÉTAPE 1 : Collecte des données via outils ─────────────────
            historique  = extraire_historique_emojis_enfant(username_enfant)
            humeur      = analyser_humeur_semaine(username_enfant)
            risque_texte = evaluer_niveau_risque(username_enfant)
            niveau       = _extraire_niveau_depuis_texte(risque_texte)

            messages_statut.append(f"✅ Données collectées. Niveau : {niveau}")

            # ── ÉTAPE 2 : Analyse IA avec tout le contexte ────────────────
            llm = _get_llm()

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", (
                    "Tu es un expert en bien-être émotionnel de l'enfant. "
                    "Analyse le profil complet de l'enfant et fournis : "
                    "1. Une évaluation de son état émotionnel actuel. "
                    "2. Des conseils concrets pour le parent ou superviseur. "
                    "3. Des recommandations de suivi. "
                    "Sois bienveillant, précis et actionnable."
                )),
                ("user", (
                    "Voici le contexte complet de l'enfant '{username}' :\n\n"
                    "=== HISTORIQUE ÉMOJIS ===\n{historique}\n\n"
                    "=== HUMEUR SEMAINE ===\n{humeur}\n\n"
                    "=== ÉVALUATION RISQUE ===\n{risque}\n\n"
                    "Génère une analyse complète et des recommandations."
                ))
            ])

            chain = prompt_template | llm | StrOutputParser()
            analyse_complete = chain.invoke({
                "username":  username_enfant,
                "historique": historique,
                "humeur":     humeur,
                "risque":     risque_texte,
            })

            # ── ÉTAPE 3 : Actions automatiques si ÉLEVÉ ou CRITIQUE ───────
            if niveau in ("ÉLEVÉ", "CRITIQUE"):

                # Email automatique au superviseur
                resultat_email = envoyer_alerte_email_superviseur(
                    username_enfant=username_enfant,
                    niveau_risque=niveau,
                    analyse_ia=analyse_complete,
                )
                email_envoye = "✅" in resultat_email
                messages_statut.append(resultat_email)

                # Notification interne dans la plateforme
                resultat_notif = creer_notification_interne(
                    username_enfant=username_enfant,
                    titre=f"Alerte {niveau} détectée",
                    message=analyse_complete[:500],  # résumé pour la notif
                )
                notification_creee = "✅" in resultat_notif
                messages_statut.append(resultat_notif)

            else:
                messages_statut.append("ℹ️ Niveau faible/modéré — aucune alerte envoyée.")

            return AnalyseComportementsType(
                niveau_risque=niveau,
                analyse_complete=analyse_complete,
                email_envoye=email_envoye,
                notification_creee=notification_creee,
                message_statut=" | ".join(messages_statut),
            )

        except Exception as e:
            print(f"❌ [ERREUR ANALYSE COMPLÈTE] : {e}")
            return AnalyseComportementsType(
                niveau_risque="INCONNU",
                analyse_complete=f"Erreur lors de l'analyse : {str(e)}",
                email_envoye=False,
                notification_creee=False,
                message_statut=f"Erreur : {str(e)}",
            )
