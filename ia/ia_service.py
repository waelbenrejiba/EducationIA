import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

class PsychologieAIService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        
        self.model = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.7,
            groq_api_key=api_key,
            timeout=10
        )
        self.output_parser = StrOutputParser()

    def generer_conseils_evolutifs(self, actuel: dict, precedent: dict = None) -> str:
        print("====== 1. Entrée dans le service IA ======")
        
        if precedent:
            print("====== 2. Historique trouvé ======")
            contexte_historique = (
                f"Le mois dernier, l'utilisateur avait ces scores :\n"
                f"- Sommeil : {precedent.score_sommeil}/100\n"
                f"- Sport : {precedent.score_sport}/100\n"
                f"- Stress : {precedent.niveau_stress}/5\n"
                f"Fais une comparaison directe pour l'encourager s'il a progressé ou l'alerter s'il a régressé."
            )
        else:
            print("====== 2. Pas d'historique (Premier quiz) ======")
            contexte_historique = "C'est le tout premier quiz de l'utilisateur, il n'y a pas d'historique pour le mois précédent."

        system_prompt = (
            "Tu es un psychologue clinicien et coach en bien-être. Ton rôle est d'analyser les scores actuels "
            "d'un utilisateur et de les comparer avec ses scores du mois précédent pour analyser sa courbe de vie.\n\n"
            "Directives :\n"
            "- Sois très précis : si un score s'est amélioré, dis-le explicitement.\n"
            "- Si un score a baissé, propose une solution bienveillante.\n"
            "- Reste synthétique (max 150 mots) avec un tutoiement chaleureux."
        )

        # CORRECTION : On liste explicitement les variables sans injecter de dictionnaire brut
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", (
                f"{contexte_historique}\n\n"
                "Voici ses scores ACTUELS pour ce mois-ci :\n"
                "- Sommeil actuel : {score_sommeil}/100\n"
                "- Sport actuel : {score_sport}/100\n"
                "- Stress actuel : {niveau_stress}/5\n"
                "- Humeur actuelle : {humeur}\n\n"
                "Génère ton analyse comparative."
            ))
        ])

        print("====== 3. Pipeline LangChain prêt ======")
        chain = prompt_template | self.model | self.output_parser

        try:
            print("====== 4. ENVOI À GROQ EN COURS... ======")
            resultat = chain.invoke({
                "score_sommeil": actuel.get("score_sommeil"),
                "score_sport": actuel.get("score_sport"),
                "niveau_stress": actuel.get("niveau_stress"),
                "humeur": actuel.get("humeur")
            })
            print("====== 5. RÉPONSE REÇUE DE GROQ AVEC SUCCÈS ! ======")
            return resultat
        except Exception as e:
            print(f"====== ❌ ERREUR INTERCEPTÉE : {str(e)} ======")
            return "Prends soin de toi ! Ton coach IA étudie tes progrès."