import json
import pandas as pd
from sqlalchemy.sql.functions import user

from backend.core.config import OLLAMA_MODEL
import ollama
from db_connection import engine

model = OLLAMA_MODEL

kpi_catalogue = """
KPIs disponibles:
    - "marge" :  marge bénéficiaire en % (profit / ventes * 100)
    - "croissance" : taux de croissance des ventes d'une année sur l'autre, en %
    - "panier_moyen" : montant moyen d'une commande
    - "remise_moyenne": taux de remise moyen appliqué, en%
    
Filtres possibles (optionnels):
- "category": Office Supplies, Technology, ou Furniture
- "year" : une année entre 2011 et 2014
"""


system_prompt = f"""
Tu identifies quel indicateur (KPI) métier est demandé dans une question, 
et tu extrais les filtres mentionnés.

{kpi_catalogue}

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour , au format exact:
{{"kpi":"nom_du_kpi", "filters": {{"category": "...", "year": "..."}}}}

Si aucun filtre n'est mentionné, renvoie un objet "filters" vide : {{}}.
Si la question ne correspond à AUCUN KPI du catalogue, réponds :
{{"kpi": null, "filters": {{}}}}

Exemples :

Question : "Quelle est la marge sur la catégorie Technology ?"
Réponse : {{"kpi": "marge", "filters": {{"category": "Technology" }}}}

Question : "Quelle a été la croissance des ventes en 2013 ?"
Réponse : {{"kpi": "croissance", "filters": {{"year": 2013}}}}
 
Question : "Quel est le panier moyen ?"
Réponse : {{"kpi": "panier_moyen", "filters": {{}}}}

"""


def classify_request(metric: str, context: str="")->dict:
    question = f"{metric} : {context}".strip()

    response = ollama.chat(
        model=model,
        messages=[
            {"role":"system", "content":system_prompt},
            {"role":"user", "content":question},
        ],
    )

    raw = response["message"]["content"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:

        parsed = {"kpi": None, "filters": {}}


    return parsed



def _build_where_clause(filters: dict, alias_product="p", alias_time="t")->str:
    conditions = []

    category = filters.get("category")

    if category in ("Office Supplies", "Technology", "Furniture"):
        conditions.append(f"{alias_product}.category = '{category}'")


    year = filters.get("year")

    if isinstance(year, int) and 2011 <= year <= 2014:
        conditions.append(f"{alias_time}.year = {year}")

    if not conditions:
        return ""

    return "WHERE " + " AND ".join(conditions)

def kpi_marge(filters: dict) -> dict:
    where = _build_where_clause(filters)
    sql = f"""
        SELECT SUM(f.profit) AS total_profit, SUM(f.sales) AS total_sales
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_time t ON f.order_date_id = t.date_id
        {where};
    """
    row = pd.read_sql(sql, engine).iloc[0]
    if row["total_sales"] in (0, None):
        return {"kpi": "marge", "value": None, "note": "Aucune donnée pour ce filtre"}
    marge = round(float(row["total_profit"]) / float(row["total_sales"]) * 100, 2)
    return {"kpi": "marge", "value_pct": marge, "filters_applied": filters}

def kpi_croissance(filters: dict)->dict:
    year = filters.get("year")

    if not year:
        return {"kpi": "croissance", "error":"Une année est requise pour ce calcul."}

    where = _build_where_clause({k: v for k, v in filters.items() if k!="year"})

    sql = f"""
         SELECT t.year, SUM(f.sales) AS total_sales
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_time t ON f.order_date_id = t.date_id
        {where}
        {"AND" if where else "WHERE"} t.year IN ({year}, {year - 1})
        GROUP BY t.year;
    """

    df = pd.read_sql(sql, engine)
    sales_by_year = dict(zip(df["year"], df["total_sales"]))

    if year not in sales_by_year or (year-1) not in sales_by_year:
        return {"kpi":"croissance", "value": None, "note":"Données insuffisantes pour comparer ces deux années"}

    growth = round((sales_by_year[year] - sales_by_year[year - 1]) / sales_by_year[year - 1] * 100, 2)
    return {"kpi": "croissance", "year": year, "value_pct": growth, "filters_applied": filters}


def kpi_panier_moyen(filters: dict) -> dict:
    where = _build_where_clause(filters)
    sql = f"""
        SELECT f.order_id, SUM(f.sales) AS order_total
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_time t ON f.order_date_id = t.date_id
        {where}
        GROUP BY f.order_id;
    """
    df = pd.read_sql(sql, engine)
    if df.empty:
        return {"kpi": "panier_moyen", "value": None, "note": "Aucune donnée pour ce filtre"}
    panier_moyen = round(df["order_total"].mean(), 2)
    return {"kpi": "panier_moyen", "value": panier_moyen, "filters_applied": filters}


def kpi_remise_moyenne(filters: dict) -> dict:
    where = _build_where_clause(filters)
    sql = f"""
        SELECT AVG(f.discount) AS avg_discount
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_time t ON f.order_date_id = t.date_id
        {where};
    """
    row = pd.read_sql(sql, engine).iloc[0]
    if row["avg_discount"] is None:
        return {"kpi": "remise_moyenne", "value": None, "note": "Aucune donnée pour ce filtre"}
    remise = round(float(row["avg_discount"]) * 100, 2)
    return {"kpi": "remise_moyenne", "value_pct": remise, "filters_applied": filters}


kpi_functions = {
    "marge": kpi_marge,
    "croissance": kpi_croissance,
    "panier_moyen": kpi_panier_moyen,
    "remise_moyenne": kpi_remise_moyenne,
}

def analytics_agent(metric: str, context: str="")->dict:
    print(f" [analytics_agent] Indicateur demandé : {metric} ({context})")

    classification = classify_request(metric, context)
    kpi_name = classification.get("kpi")
    filters = classification.get("filters", {})

    print(f"   [analytics_agent] KPI identifié : {kpi_name}, filtres : {filters}")

    if kpi_name not in kpi_functions:
        return {
            "error": f"Aucun KPI reconnu pour cette demande. KPIs disponibles : {list(kpi_functions.keys())}"
        }

    function = kpi_functions[kpi_name]
    result = function(filters)
    print(f"   [analytics_agent] Résultat : {result}")
    return result


if __name__ == "__main__":
    tests = [
        ("marge", "sur la catégorie Technology"),
        ("croissance des ventes", "en 2013"),
        ("panier moyen", ""),
        ("taux de remise moyen", ""),
    ]

    for metric, context in tests:
        print("\n" + "=" * 60)
        result = analytics_agent(metric, context)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
