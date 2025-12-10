# services/assistant_ai.py

import json
from openai import OpenAI


class GPTAssistant:
    """
    Assistant IA spécialisé dans l'analyse immobilière.
    Compatible avec le SDK OpenAI 2025 (client.responses).
    """

    def __init__(self, model="gpt-5-mini"):
        self.client = OpenAI()     # pas de clé ici
        self.model = model

    # ------------------------------------------------------------------
    # Construction du prompt
    # ------------------------------------------------------------------
    def build_prompt(
        self,
        city1, city2,
        stats_city1, stats_city2,
        weekly_city1, weekly_city2,
        geo_city1, geo_city2,
        user_question
    ):
        prompt = f"""
Tu es un expert en analyse immobilière, spécialisé dans l'interprétation de 
tableaux de bord de données (dashboard analytics).

Tu dois analyser à quelqu'un qui ne s'y connait pas les données de deux villes et expliquer , résumer le plus simplement possible :
- leurs tendances immobilières
- leurs différences structurelles
- ce que racontent les courbes de prix médians
- ce que montrent les cartes de densité et de prix
- les insights les plus importants

-----------------------------------------------------
Ville 1 : {city1}
-----------------------------------------------------
Statistiques globales :
{json.dumps(stats_city1, indent=2, ensure_ascii=False)}

Tendance hebdomadaire (prix médian lissé) :
{weekly_city1}

Résumé géographique :
{json.dumps(geo_city1, indent=2, ensure_ascii=False)}

-----------------------------------------------------
Ville 2 : {city2}
-----------------------------------------------------
Statistiques globales :
{json.dumps(stats_city2, indent=2, ensure_ascii=False)}

Tendance hebdomadaire (prix médian lissé) :
{weekly_city2}

Résumé géographique :
{json.dumps(geo_city2, indent=2, ensure_ascii=False)}

-----------------------------------------------------
Question utilisateur :
"{user_question}"
-----------------------------------------------------

Mission :
Analyse les tendances et réponds clairement à la question.
Structure ta réponse :
1. Résumé global en 3 phrases
2. Analyse des tendances temporelles
3. Comparaison des deux villes
4. Analyse géographique
5. Insight final à retenir
Veille à utiliser un langage clair et accessible. 
        """

        return prompt.strip()

    # ------------------------------------------------------------------
    # Appel au modèle GPT
    # ------------------------------------------------------------------
    def ask(self, prompt):
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )
        return response.output_text

    # ------------------------------------------------------------------
    # Méthode principale
    # ------------------------------------------------------------------
    def analyze(
        self,
        city1, city2,
        stats_city1, stats_city2,
        weekly_city1, weekly_city2,
        geo_city1, geo_city2,
        user_question
    ):
        prompt = self.build_prompt(
            city1, city2,
            stats_city1, stats_city2,
            weekly_city1, weekly_city2,
            geo_city1, geo_city2,
            user_question
        )

        return self.ask(prompt)
