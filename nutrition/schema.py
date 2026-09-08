import graphene
from graphene_django import DjangoObjectType
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from django.conf import settings
import os
from .models import ProfilNutritionnel

class ProfilNutritionnelType(DjangoObjectType):
    imc = graphene.Float()

    class Meta:
        model = ProfilNutritionnel
        fields = ("id", "poids", "taille", "fruits_legumes_favoris", "cree_le")

    def resolve_imc(self, info):
        return self.imc

class RecetteSanteType(graphene.ObjectType):
    recette = graphene.String()
    conseils_nutritionnels = graphene.String()
    imc_info = graphene.String()

# --- MUTATION : Sauvegarder le profil ---
class SauvegarderProfilMutation(graphene.Mutation):
    class Arguments:
        poids = graphene.Float(required=True)
        taille = graphene.Float(required=True)
        fruits_legumes_favoris = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    profil = graphene.Field(ProfilNutritionnelType)

    def mutate(self, info, poids, taille, fruits_legumes_favoris):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("🔐 Connectez-vous pour sauvegarder votre profil.")

        profil, created = ProfilNutritionnel.objects.update_or_create(
            user=user,
            defaults={
                "poids": poids,
                "taille": taille,
                "fruits_legumes_favoris": fruits_legumes_favoris
            }
        )
        action = "créé" if created else "mis à jour"
        return SauvegarderProfilMutation(
            success=True,
            message=f"Profil nutritionnel {action} avec succès.",
            profil=profil
        )

# --- QUERY : Générer la recette IA ---
class Query(graphene.ObjectType):
    generer_recette_sante = graphene.Field(RecetteSanteType)
    mon_profil_nutritionnel = graphene.Field(ProfilNutritionnelType)

    def resolve_mon_profil_nutritionnel(self, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        try:
            return ProfilNutritionnel.objects.get(user=user)
        except ProfilNutritionnel.DoesNotExist:
            return None

    def resolve_generer_recette_sante(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("🔐 Connectez-vous pour obtenir une recette.")

        try:
            profil = ProfilNutritionnel.objects.get(user=user)
        except ProfilNutritionnel.DoesNotExist:
            raise Exception("❌ Remplissez d'abord votre profil nutritionnel.")

        imc = profil.imc
        if imc < 18.5:
            statut_imc = "insuffisance pondérale"
        elif imc < 25:
            statut_imc = "poids normal"
        elif imc < 30:
            statut_imc = "surpoids"
        else:
            statut_imc = "obésité"

        api_key = os.environ.get('GROQ_API_KEY', getattr(settings, 'GROQ_API_KEY', None))
        if not api_key:
            return RecetteSanteType(
                recette="Clé API manquante.",
                conseils_nutritionnels="Configurez GROQ_API_KEY.",
                imc_info=f"IMC: {imc} ({statut_imc})"
            )

        try:
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0.5,
                groq_api_key=api_key,
                timeout=30
            )
            output_parser = StrOutputParser()

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", (
                    "Tu es un nutritionniste expert. En fonction du profil de l'utilisateur, "
                    "génère une recette détaillée, saine et savoureuse qui utilise ses fruits et légumes favoris. "
                    "Adapte la recette à son IMC. Inclus : nom de la recette, ingrédients avec quantités, "
                    "étapes de préparation, valeurs nutritionnelles estimées, et 3 conseils santé personnalisés."
                )),
                ("user", (
                    "Mon profil :\n"
                    "- Poids : {poids} kg\n"
                    "- Taille : {taille} cm\n"
                    "- IMC : {imc} ({statut_imc})\n"
                    "- Fruits et légumes favoris : {fruits_legumes}\n"
                    "Génère une recette santé détaillée adaptée à mon profil."
                ))
            ])

            chain = prompt_template | llm | output_parser
            recette_ia = chain.invoke({
                "poids": profil.poids,
                "taille": profil.taille,
                "imc": imc,
                "statut_imc": statut_imc,
                "fruits_legumes": profil.fruits_legumes_favoris
            })

            return RecetteSanteType(
                recette=recette_ia,
                conseils_nutritionnels="Recette générée par IA nutritionniste (Groq/LangChain)",
                imc_info=f"IMC: {imc} ({statut_imc})"
            )

        except Exception as e:
            print(f"❌ [ERREUR GROQ NUTRITION] : {e}")
            return RecetteSanteType(
                recette=f"Erreur IA : {str(e)}",
                conseils_nutritionnels="Erreur moteur LangChain",
                imc_info=f"IMC: {imc} ({statut_imc})"
            )

class Mutation(graphene.ObjectType):
    sauvegarder_profil = SauvegarderProfilMutation.Field()