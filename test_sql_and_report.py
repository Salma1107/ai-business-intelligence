import json
from sql_agent import sql_agent
from report_agent import report_agent


def run_pipeline(question: str):
    print("\n" + "=" * 70)
    print(f"QUESTION : {question}")
    print("=" * 70)

    sql_result = sql_agent(question)

    if "error" in sql_result:
        print(f"SQL Agent a échoué : {sql_result['error']}")
        return

    if not sql_result["rows"]:
        print("Aucune ligne renvoyée par la requête.")
        return

    row = sql_result["rows"][0]
    results_text = f"Produit : {row['product_name']}, ventes totales : {row['total_sales']:.2f}$"

    report = report_agent(results_text)

    print("\n--- RAPPORT FINAL ---")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    questions = [
        "Quel est le produit qui a généré le plus de ventes au total ?",
        "Quelle est la région avec le plus de profit ?",
    ]

    for q in questions:
        run_pipeline(q)