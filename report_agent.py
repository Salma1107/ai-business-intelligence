import json

from backend.core.config import OLLAMA_MODEL
import ollama

MODEL = OLLAMA_MODEL

SYSTEM_PROMPT = """Tu rédiges un rapport business synthétique à partir de résultats de données
déjà calculés (fournis par d'autres systèmes, pas par toi).

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour, au format exact :
{
  "title": "Titre court du rapport",
  "summary": "Un paragraphe de synthèse en langage naturel, clair et professionnel",
  "key_points": ["point clé 1", "point clé 2", ...]
}

Règles :
- Le titre fait moins de 8 mots.
- Le résumé ne doit contenir AUCUN chiffre inventé : utilise uniquement les valeurs
  fournies dans les résultats.
- 2 à 4 points clés maximum, chacun une phrase courte.
- N'utilise jamais de markdown (pas de **, pas de #).
- Sémantique obligatoire des mesures : `sales` et `total_sales` sont des MONTANTS
  de ventes / chiffres d'affaires ; ne les appelle jamais "unités", "quantités"
  ou "volume". `quantity` et `total_quantity` sont, eux, des unités vendues.
- Utilise exclusivement les faits et mesures présents dans les résultats fournis.
- N'affirme jamais qu'une valeur est supérieure, inférieure, meilleure, pire, en
  hausse, en baisse ou en tendance, sauf si les valeurs de comparaison nécessaires
  sont explicitement présentes dans les résultats. Si elles ne sont pas fournies,
  ne mentionne pas de comparaison ni de conclusion interprétative.

Exemple :

Résultats fournis : "Produit le plus vendu : Staples, quantité totale : 876 unités."
Réponse :
{
  "title": "Produit le plus vendu",
  "summary": "L'analyse des ventes cumulées montre que Staples est le produit le plus vendu, avec un total de 876 unités écoulées.",
  "key_points": ["Staples est en tête des ventes en volume", "876 unités vendues au total"]
}
"""


def _metric_semantics_guidance(results: str) -> str:
    normalized_results = results.lower()
    guidance = []

    if "sales" in normalized_results:
        guidance.append(
            "Toute valeur `sales` ou `total_sales` est un montant des ventes ou un chiffre d'affaires, jamais une quantité."
        )
    if "quantity" in normalized_results:
        guidance.append(
            "Toute valeur `quantity` ou `total_quantity` représente un nombre d'unités vendues."
        )

    return "\n".join(guidance)


def report_agent(results: str) -> dict:
    print(f"   [report_agent] Synthèse à partir de : {results}")


    has_digit = any(char.isdigit() for char in results)
    is_too_short = len(results.strip()) < 15

    if not has_digit or is_too_short:
        print("   [report_agent] Données insuffisantes ou non exploitables -> refus de générer un rapport")
        return {
            "error": (
                "Impossible de générer un rapport : aucune donnée réelle exploitable "
                "n'a été fournie. Il faut d'abord obtenir un résultat via sql_agent, "
                "analytics_agent ou forecast_agent."
            )
        }

    metric_guidance = _metric_semantics_guidance(results)
    report_input = results
    if metric_guidance:
        report_input += f"\n\nRègles de sémantique des mesures :\n{metric_guidance}"

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": report_input},
        ],
    )
    raw = response["message"]["content"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        report = {
            "title": "Rapport",
            "summary": raw,
            "key_points": [],
        }

    print(f"   [report_agent] Rapport généré : {report}")
    return report


if __name__ == "__main__":
    tests = [
        "Produit le plus vendu : Staples, quantité totale : 876 unités.",
        "Marge sur la catégorie Technology : 13.99%. Croissance des ventes en 2013 : 27.2%.",
        "Prévision des ventes Technology pour le mois prochain : 152000 euros, "
        "intervalle de confiance entre 140000 et 164000 euros.",
    ]

    for r in tests:
        print("\n" + "=" * 60)
        result = report_agent(r)
        print(json.dumps(result, indent=2, ensure_ascii=False))
