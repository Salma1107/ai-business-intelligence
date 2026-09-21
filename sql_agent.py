import re
import json
import pandas as pd
from time import perf_counter

from backend.core.config import OLLAMA_MODEL
import ollama
from db_connection import engine

MODEL = OLLAMA_MODEL

SCHEMA_DESCRIPTION = """
Tables disponibles (PostgreSQL) :

fact_sales (table de faits)
  - row_id, order_id
  - product_key   (-> dim_product.product_key)
  - customer_id   (-> dim_customer.customer_id)
  - geography_id  (-> dim_geography.geography_id)
  - order_date_id (-> dim_time.date_id)
  - ship_date_id  (-> dim_time.date_id)
  - order_priority, ship_mode
  - sales, profit, quantity, discount, shipping_cost

dim_product
  - product_key (clé primaire), product_id, product_name, category, sub_category

dim_customer
  - customer_id (clé primaire), customer_name, segment

dim_geography
  - geography_id (clé primaire), city, state, country, region, market, market2

dim_time
  - date_id (clé primaire), full_date, year, month, day, weeknum, day_of_week, quarter
"""

SYSTEM_PROMPT = f"""Tu es un générateur de requêtes SQL PostgreSQL.

Voici le schéma de la base de données :
{SCHEMA_DESCRIPTION}

Règles strictes :
- Réponds UNIQUEMENT avec la requête SQL, sans aucune explication, sans markdown, sans ```.
- Toujours une requête SELECT (jamais INSERT, UPDATE, DELETE, DROP...).
- Une seule instruction SQL, pas de point-virgule multiple.
- Utilise UNIQUEMENT les tables et colonnes explicitement présentes dans le schéma ci-dessus.
- Il est strictement interdit d'inventer une table, une colonne, une relation ou une dimension.
- `ship_mode` et `order_priority` sont des colonnes de `fact_sales` : ne les joins jamais
  à des tables de dimension, car aucune table `dim_ship_mode` ou `dim_order_priority` n'existe.
- Utilise les jointures nécessaires entre fact_sales et les dimensions.
- Termine la requête par un point-virgule.

Règles d'interprétation IMPORTANTES :
- "le plus vendu", "le meilleur", "le total le plus élevé", "qui a généré le plus de X"
  signifient TOUJOURS une somme agrégée (SUM) regroupée (GROUP BY), jamais une seule
  ligne/transaction individuelle. Ne JAMAIS répondre avec un simple ORDER BY ... LIMIT 1
  sur une colonne brute de fact_sales sans agrégation préalable.
- "une commande", "une vente", "une transaction" (au singulier, explicite) signifient
  une ligne individuelle de fact_sales, sans agrégation.
- Quand la question utilise un singulier ("quel est LE produit...", "quelle est LA
  région..."), la requête doit TOUJOURS se terminer par LIMIT 1, pour ne renvoyer
  qu'une seule ligne.
- Quand la question demande un nombre précis d'éléments ("les 5 meilleurs", "le top 3"),
  utilise LIMIT avec ce nombre exact.
- Si la question ne précise aucune limite ni singulier/pluriel explicite, n'ajoute pas
  de LIMIT.

Exemples :

Question : "Quel est le produit qui a généré le plus de ventes au total ?"
Requête :
SELECT p.product_name, SUM(f.sales) AS total_sales
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name
ORDER BY total_sales DESC
LIMIT 1;

Question : "Quelle est la plus grosse vente individuelle jamais enregistrée ?"
Requête :
SELECT p.product_name, f.sales
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
ORDER BY f.sales DESC
LIMIT 1;

Question : "Quel est le total des profits par catégorie ?"
Requête :
SELECT p.category, SUM(f.profit) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category;

Question : "Quelles sont les 5 régions avec le plus de profit ?"
Requête :
SELECT g.region, SUM(f.profit) AS total_profit
FROM fact_sales f
JOIN dim_geography g ON f.geography_id = g.geography_id
GROUP BY g.region
ORDER BY total_profit DESC
LIMIT 5;
"""


def generate_sql(question: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    raw_sql = response["message"]["content"].strip()

    raw_sql = raw_sql.replace("```sql", "").replace("```", "").strip()
    return raw_sql



FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter",
    "truncate", "grant", "revoke", "create", "exec",
]


ALLOWED_TABLES = {
    "fact_sales",
    "dim_product",
    "dim_customer",
    "dim_geography",
    "dim_time",
}

USER_SQL_ERROR_MESSAGE = (
    "Je ne peux pas répondre à cette question avec les données actuellement disponibles. "
    "Veuillez poser une question BI mesurable à partir des ventes, produits, catégories, régions ou périodes disponibles."
)

def validate_sql(sql: str) -> tuple[bool, str]:
    cleaned = sql.strip().lower()

    if not cleaned.startswith("select"):
        return False, "La requête ne commence pas par SELECT."

    for word in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{word}\b", cleaned):
            return False, f"Mot-clé interdit détecté : {word.upper()}"

    if cleaned.count(";") > 1:
        return False, "Plusieurs instructions SQL détectées (un seul ';' autorisé, en fin de requête)."

    referenced_tables = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", cleaned)
    unknown_tables = sorted({table for table in referenced_tables if table not in ALLOWED_TABLES})
    if unknown_tables:
        return False, f"Table inconnue détectée : {', '.join(unknown_tables)}"

    return True, ""


SINGULAR_PATTERNS = [
    r"\bquel est le\b", r"\bquelle est la\b", r"\bquel produit\b",
    r"\bquelle région\b", r"\bquel client\b", r"\ble plus\b(?!.*\bles\b)",
    r"\bla plus\b",
]

BREAKDOWN_PATTERNS = [
    r"\bpar catégorie\b", r"\bpar région\b", r"\bpar produit\b",
    r"\bpar client\b", r"\bpar segment\b", r"\bpar année\b",
    r"\bpar mois\b", r"\bpar jour\b", r"\bpar marché\b",
]

def expects_single_row(question: str) -> bool:
    q = question.lower()

    if re.search(r"\d+", q):
        return False

    if any(re.search(p, q) for p in BREAKDOWN_PATTERNS):
        return False
    return any(re.search(p, q) for p in SINGULAR_PATTERNS)


def enforce_limit_if_needed(sql: str, question: str) -> str:
    cleaned = sql.strip().rstrip(";").strip()
    has_limit = re.search(r"\blimit\s+\d+\b", cleaned.lower()) is not None

    if expects_single_row(question) and not has_limit:
        print("   [sql_agent] LIMIT manquant pour une question au singulier -> ajout automatique de LIMIT 1")
        cleaned += " LIMIT 1"

    return cleaned + ";"



def execute_sql(sql: str) -> list[dict]:
    df = pd.read_sql(sql, engine)
    return df.to_dict(orient="records")



def sql_agent(question: str) -> dict:
    agent_started_at = perf_counter()
    print(f"   [sql_agent] Question reçue : {question}")

    sql_generation_started_at = perf_counter()
    sql = generate_sql(question)
    print(f"[PERF] sql_generation_llm = {perf_counter() - sql_generation_started_at:.2f}s")
    print(f"   [sql_agent] SQL généré :\n   {sql}")

    sql = enforce_limit_if_needed(sql, question)

    is_safe, reason = validate_sql(sql)
    if not is_safe:
        print(f"   [sql_agent] Validation SQL refusée : {reason}")
        print(f"[PERF] sql_agent = {perf_counter() - agent_started_at:.2f}s")
        return {"error": USER_SQL_ERROR_MESSAGE}

    try:
        postgres_started_at = perf_counter()
        rows = execute_sql(sql)
        print(f"[PERF] postgres = {perf_counter() - postgres_started_at:.2f}s")
    except Exception as e:
        print(f"   [sql_agent] Erreur d'exécution : {e}")
        print(f"[PERF] sql_agent = {perf_counter() - agent_started_at:.2f}s")
        return {"error": USER_SQL_ERROR_MESSAGE}

    print(f"   [sql_agent] {len(rows)} ligne(s) renvoyée(s)")
    print(f"[PERF] sql_agent = {perf_counter() - agent_started_at:.2f}s")
    return {"sql_used": sql, "rows": rows}


if __name__ == "__main__":
    test_questions = [
        "Quel est le produit qui a généré le plus de ventes au total ?",
        "Quel est le total des profits par catégorie de produit ?",
        "Quelles sont les 5 régions avec le plus de profit ?",
    ]

    for q in test_questions:
        print("\n" + "=" * 60)
        result = sql_agent(q)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
