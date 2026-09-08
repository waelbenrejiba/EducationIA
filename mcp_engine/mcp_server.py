"""
mcp_server.py — mcp_engine
Serveur MCP autonome : expose les outils Django au LLM via le protocole MCP.
Lancer séparément avec : python mcp_server.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "newgen.settings")
django.setup()

from mcp.server.fastmcp import FastMCP

# Import des fonctions pures depuis tools.py
from mcp_engine.tools import (
    extraire_historique_emojis_enfant,
    analyser_humeur_semaine,
    evaluer_niveau_risque,
    envoyer_alerte_email_superviseur,
    creer_notification_interne,
    get_profil_nutritionnel,
)

mcp = FastMCP("MCP_Newgen_Enfants")


# ── Enregistrement des outils MCP (décorateurs seulement ici) ────────────────

@mcp.tool()
def tool_historique_emojis(username_enfant: str) -> str:
    """Récupère les 5 dernières alertes/émojis envoyés par l'enfant."""
    return extraire_historique_emojis_enfant(username_enfant)


@mcp.tool()
def tool_humeur_semaine(username_enfant: str) -> str:
    """Analyse les états émotionnels de l'enfant sur les 7 derniers jours."""
    return analyser_humeur_semaine(username_enfant)


@mcp.tool()
def tool_niveau_risque(username_enfant: str) -> str:
    """
    Calcule le niveau de risque : FAIBLE / MODÉRÉ / ÉLEVÉ / CRITIQUE.
    Toujours appeler avant toute décision d'alerte.
    """
    return evaluer_niveau_risque(username_enfant)


@mcp.tool()
def tool_email_superviseur(
    username_enfant: str,
    niveau_risque: str,
    analyse_ia: str
) -> str:
    """
    Envoie un email HTML d'alerte au superviseur.
    Appeler UNIQUEMENT si niveau_risque est ÉLEVÉ ou CRITIQUE.
    """
    return envoyer_alerte_email_superviseur(username_enfant, niveau_risque, analyse_ia)


@mcp.tool()
def tool_notification_interne(
    username_enfant: str,
    titre: str,
    message: str
) -> str:
    """
    Crée une notification interne dans la plateforme.
    Complément à l'email pour tracer l'intervention IA.
    """
    return creer_notification_interne(username_enfant, titre, message)


@mcp.tool()
def tool_profil_nutritionnel(username_enfant: str) -> str:
    """Récupère le profil nutritionnel pour enrichir l'analyse bien-être."""
    return get_profil_nutritionnel(username_enfant)


# ── Point d'entrée ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Serveur MCP Newgen démarré...")
    mcp.run()
