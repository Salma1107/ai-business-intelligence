import json
import inspect
from numbers import Number
from time import perf_counter

from backend.core.config import OLLAMA_MODEL
import ollama
from sql_agent import sql_agent
from analytics_agent import analytics_agent
from report_agent import report_agent
from forecast_agent import forecast_agent


model = OLLAMA_MODEL

tools = [
    {
        "type": "function",
        "function": {
            "name": "sql_agent",
            "description": (
                "Interroge la base de données de ventes (schéma en étoile PostgreSQL) "
                "pour répondre à des questions FACTUELLES sur des données existantes : "
                "chiffres bruts, comparaisons, tops/flops, filtres par date, région, catégorie. "
                "Ne PAS utiliser pour des questions portant sur le futur (utiliser forecast_agent). "
                "NE JAMAIS utiliser pour calculer une marge, un taux de croissance, un panier "
                "moyen ou un taux de remise : ce sont des indicateurs avec une formule précise, "
                "réservés à analytics_agent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "La question reformulée simplement, en langage naturel",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analytics_agent",
            "description": (
                "Calcule des indicateurs métier (KPIs) à partir de données déjà "
                "récupérées : marge, taux de croissance, moyennes, tendances. "
                "À utiliser APRÈS le sql_agent si un calcul supplémentaire est nécessaire."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "L'indicateur demandé, ex: 'marge', 'taux de croissance'",
                    },
                    "context": {
                        "type": "string",
                        "description": "Contexte ou filtre, ex: 'catégorie Technology en 2013'",
                    },
                },
                "required": ["metric"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_agent",
            "description": (
                "Prédit les ventes futures à partir de l'historique, via un modèle "
                "de Deep Learning (LSTM). À utiliser UNIQUEMENT si la question porte "
                "sur l'avenir (mots-clés : 'prévois', 'quel sera', 'estime pour')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "horizon": {
                        "type": "string",
                        "description": "Période à prévoir, ex: '1 mois', '3 semaines'",
                    },
                    "segment": {
                        "type": "string",
                        "description": "Filtre optionnel : catégorie, région, etc.",
                    },
                },
                "required": ["horizon"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_agent",
            "description": (
                "Synthétise les résultats des autres agents en un RAPPORT STRUCTURÉ "
                "(titre, résumé, points clés), destiné à l'écran Rapports de l'application. "
                "À appeler EN DERNIER, une fois que les données nécessaires ont été "
                "rassemblées par les autres agents, et UNIQUEMENT si l'utilisateur demande "
                "explicitement un rapport, une synthèse ou un résumé structuré."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "string",
                        "description": "Résumé texte des résultats des agents précédents à synthétiser",
                    }
                },
                "required": ["results"],
            },
        },
    },
]


agent_functions = {
    "sql_agent": sql_agent,
    "analytics_agent": analytics_agent,
    "forecast_agent": forecast_agent,
    "report_agent": report_agent,
}

DATA_AGENT_NAMES = {"sql_agent", "analytics_agent", "forecast_agent"}
MAX_TOOL_CALLS_PER_REQUEST = 4
NON_MEASURABLE_QUESTION_MESSAGE = (
    "Je peux répondre aux questions BI mesurables sur les ventes, produits, catégories, "
    "régions et périodes disponibles. Pouvez-vous préciser l'indicateur ou la période à analyser ?"
)


ORCHESTRATOR_SYSTEM_PROMPT = """Tu es un assistant qui répond à des questions business en utilisant des outils.

Règles impératives, dans cet ordre :
1. Si la question demande une donnée factuelle, une prévision, ou un indicateur, tu DOIS
   d'abord appeler l'outil correspondant (sql_agent, analytics_agent, ou forecast_agent)
   pour obtenir les VRAIES données. Ne saute JAMAIS cette étape.
2. Si la question contient en plus les mots "rapport", "synthèse" ou "résumé", tu dois
   appeler report_agent EN DERNIER, une fois les vraies données obtenues. Le paramètre
   "results" doit contenir les VALEURS RÉELLES renvoyées par les outils précédents
   (chiffres, noms de produits...), JAMAIS le nom d'un outil ou un texte vide de sens.
3. N'appelle jamais report_agent en premier, ni avec des données que tu n'as pas
   réellement obtenues via un autre outil.
"""


def _looks_like_fake_tool_call(text: str) -> bool:

    lowered = text.lower()
    has_name_field = '"name":' in lowered or "'name':" in lowered
    has_params_field = '"parameters"' in lowered or "'parameters'" in lowered or '"results"' in lowered
    return has_name_field and has_params_field


def _format_collected_results(collected_results: list) -> str:

    if not collected_results:
        return ""
    lines = []
    for agent_name, agent_input, result in collected_results:
        lines.append(f"Résultat de {agent_name} (entrée : {agent_input}) : {json.dumps(result, ensure_ascii=False)}")
    return "\n".join(lines)


def _is_report_request(question: str) -> bool:
    normalized_question = question.lower()
    return any(
        keyword in normalized_question
        for keyword in ("rapport", "synthèse", "synthese", "résumé", "resume")
    )


def _is_non_measurable_question(question: str) -> bool:
    normalized_question = question.lower()
    return any(
        expression in normalized_question
        for expression in (
            "comment améliorer",
            "comment augmenter",
            "comment booster",
            "comment optimiser les ventes",
        )
    )


def _infer_data_agent_for_report(question: str) -> tuple[str, dict]:
    normalized_question = question.lower()

    if any(keyword in normalized_question for keyword in ("prévoi", "prévision", "prochain", "futur")):
        return "forecast_agent", {"horizon": question, "segment": ""}

    analytics_keywords = (
        "marge", "croissance", "panier moyen", "remise", "taux de",
    )
    if any(keyword in normalized_question for keyword in analytics_keywords):
        return "analytics_agent", {"metric": question, "context": ""}

    return "sql_agent", {"question": question}


def _generate_report_from_inferred_source(user_question: str, total_started_at: float) -> str:
    source_agent, source_input = _infer_data_agent_for_report(user_question)
    print(
        "   [orchestrateur] Demande de rapport explicite : "
        f"source de données inférée = {source_agent}"
    )

    source_started_at = perf_counter()
    source_result = agent_functions[source_agent](**source_input)
    if source_agent != "sql_agent":
        print(f"[PERF] {source_agent} = {perf_counter() - source_started_at:.2f}s")

    if isinstance(source_result, dict) and source_result.get("error"):
        print("   [orchestrateur] Rapport non exécuté : la source n'a fourni aucune donnée exploitable")
        print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
        return _format_agent_result(source_agent, source_result, user_question)

    if source_agent == "sql_agent" and not source_result.get("rows"):
        print("   [orchestrateur] Rapport non exécuté : résultat SQL vide")
        print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
        return _format_sql_result(source_result, user_question)

    real_results_text = _format_collected_results(
        [(source_agent, source_input, source_result)]
    )
    print("   [orchestrateur] Exécution différée de report_agent après les agents producteurs")
    report_started_at = perf_counter()
    report_result = report_agent(real_results_text)
    print(f"[PERF] report_agent = {perf_counter() - report_started_at:.2f}s")
    answer = _format_agent_result("report_agent", report_result, user_question)
    print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
    return answer


def _format_value(value) -> str:
    if value is None:
        return "non disponible"
    if isinstance(value, bool):
        return "oui" if value else "non"
    if isinstance(value, Number):
        numeric_value = float(value)
        if numeric_value.is_integer():
            return f"{int(numeric_value):,}".replace(",", " ")
        return f"{numeric_value:,.2f}".replace(",", " ").replace(".", ",")
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _format_column_name(column_name: str) -> str:
    return column_name.replace("_", " ")


def _format_row(row: dict) -> str:
    return "; ".join(
        f"{_format_column_name(str(column))} : {_format_value(value)}"
        for column, value in row.items()
    )


def _is_top_sales_question(question: str) -> bool:
    normalized_question = question.lower()
    return any(
        expression in normalized_question
        for expression in ("plus vendu", "meilleur produit", "top produit")
    )


def _format_compact_row(row: dict) -> str:
    label_keys = ("product_name", "category_name", "category", "region", "region_name")
    metric_keys = ("total_sales", "total_profit", "sales", "profit", "quantity", "value")

    label = next((row[key] for key in label_keys if key in row), None)
    metric = next((row[key] for key in metric_keys if key in row), None)

    if label is not None and metric is not None:
        return f"{_format_value(label)} : {_format_value(metric)}"
    if label is not None:
        return _format_value(label)
    return _format_row(row)


def _format_sql_result(result: dict, question: str) -> str:
    rows = result.get("rows")

    if not isinstance(rows, list) or not rows:
        return "Aucun résultat n’a été trouvé pour cette question."

    if len(rows) == 1 and isinstance(rows[0], dict):
        row = rows[0]
        product_name = row.get("product_name")
        total_sales = row.get("total_sales")

        if product_name is not None and _is_top_sales_question(question):
            answer = f"Le produit le plus vendu est {_format_value(product_name)}"
            if total_sales is not None:
                answer += f", avec {_format_value(total_sales)} unités vendues"
            return answer + "."

        if product_name is not None:
            if total_sales is not None:
                return (
                    f"Le produit est {_format_value(product_name)}, avec "
                    f"{_format_value(total_sales)} unités vendues."
                )
            return f"Le produit est {_format_value(product_name)}."

        if row.get("category_name") is not None or row.get("category") is not None:
            category = row.get("category_name", row.get("category"))
            if total_sales is not None:
                return f"La catégorie {_format_value(category)} totalise {_format_value(total_sales)} ventes."
            return f"La catégorie est {_format_value(category)}."

        if row.get("region_name") is not None or row.get("region") is not None:
            region = row.get("region_name", row.get("region"))
            if total_sales is not None:
                return f"La région {_format_value(region)} totalise {_format_value(total_sales)} ventes."
            return f"La région est {_format_value(region)}."

        if total_sales is not None:
            return (
                "Le total des ventes est de "
                f"{_format_value(total_sales)}."
            )

        return f"Résultat : {_format_row(row)}."

    formatted_rows = []
    for index, row in enumerate(rows[:10], start=1):
        if isinstance(row, dict):
            formatted_rows.append(f"{index}. {_format_compact_row(row)}")
        else:
            formatted_rows.append(f"{index}. {_format_value(row)}")

    suffix = "\nRésultats supplémentaires non affichés." if len(rows) > 10 else ""
    return "Résultats :\n" + "\n".join(formatted_rows) + suffix


def _format_agent_result(agent_name: str, result, user_question: str) -> str:
    if not isinstance(result, dict):
        return _format_value(result)

    if result.get("error"):
        return str(result["error"])

    if agent_name == "report_agent" and result.get("summary"):
        return str(result["summary"])

    if agent_name == "sql_agent":
        return _format_sql_result(result, user_question)

    if agent_name == "analytics_agent":
        kpi = result.get("kpi")
        if "value_pct" in result:
            label = str(kpi).replace("_", " ") if kpi else "L’indicateur demandé"
            return f"{label.capitalize()} : {_format_value(result['value_pct'])} %."
        if "value" in result:
            label = str(kpi).replace("_", " ") if kpi else "Résultat"
            return f"{label.capitalize()} : {_format_value(result['value'])}."

    if agent_name == "forecast_agent" and "prediction" in result:
        answer = f"Prévision : {_format_value(result['prediction'])}."
        if result.get("horizon_days"):
            answer += f" Horizon : {_format_value(result['horizon_days'])} jours."
        return answer

    visible_items = [
        f"{_format_column_name(str(key))} : {_format_value(value)}"
        for key, value in result.items()
        if key != "sql_used"
    ]
    return "Résultat : " + "; ".join(visible_items) + "." if visible_items else "Aucun résultat exploitable."


def _format_agent_results(executed_results: list[tuple[str, object]], user_question: str) -> str:
    if len(executed_results) == 1:
        agent_name, result = executed_results[0]
        return _format_agent_result(agent_name, result, user_question)

    return "\n\n".join(
        f"{agent_name.replace('_', ' ').capitalize()} :\n"
        f"{_format_agent_result(agent_name, result, user_question)}"
        for agent_name, result in executed_results
    )


def ask_orchestrator(user_question: str) -> str:

    total_started_at = perf_counter()

    if _is_non_measurable_question(user_question):
        print("   [orchestrateur] Question non mesurable détectée -> aucun SQL généré")
        print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
        return NON_MEASURABLE_QUESTION_MESSAGE

    if _is_report_request(user_question):
        return _generate_report_from_inferred_source(user_question, total_started_at)

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    collected_results = []
    retries_left = 2
    routing_call_count = 0

    print(f"Question: {user_question}")

    while True:
        routing_started_at = perf_counter()
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=tools,
        )
        routing_elapsed = perf_counter() - routing_started_at
        routing_call_count += 1
        perf_label = "routing_llm" if routing_call_count == 1 else "report_routing_llm"
        print(f"[PERF] {perf_label} = {routing_elapsed:.2f}s")

        message = response["message"]
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            if _is_report_request(user_question):
                inferred_agent, inferred_input = _infer_data_agent_for_report(user_question)
                print(
                    "   [orchestrateur] Aucun outil proposé pour le rapport : "
                    f"source de données inférée = {inferred_agent}"
                )
                result = agent_functions[inferred_agent](**inferred_input)
                collected_results.append((inferred_agent, inferred_input, result))
                real_results_text = _format_collected_results(collected_results)
                print("   [orchestrateur] Exécution différée de report_agent après les agents producteurs")
                report_started_at = perf_counter()
                report_result = report_agent(real_results_text)
                print(f"[PERF] report_agent = {perf_counter() - report_started_at:.2f}s")
                answer = _format_agent_result("report_agent", report_result, user_question)
                print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
                return answer

            content = message.get("content", "")

            if _looks_like_fake_tool_call(content) and retries_left > 0:
                retries_left -= 1
                print(f"   [orchestrateur] Faux appel d'outil détecté dans le texte -> nouvelle tentative ({retries_left} restante(s))")
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": (
                        "Ta réponse précédente contenait un faux appel d'outil écrit en texte, "
                        "avec des données possiblement inventées. N'écris JAMAIS d'appel d'outil "
                        "en texte : utilise le vrai mécanisme d'appel d'outil, ou réponds "
                        "directement en langage naturel si tu as déjà les données nécessaires. "
                        "IMPORTANT : ne répète JAMAIS un chiffre ou une affirmation que tu as "
                        "proposé plus tôt dans cette conversation si elle n'a pas été confirmée "
                        "par un résultat réel d'outil — considère toute affirmation non confirmée "
                        "comme fausse et à ignorer complètement."
                    ),
                })
                continue

            if _looks_like_fake_tool_call(content) and retries_left == 0:
                print("   [orchestrateur] Faux appel d'outil détecté à nouveau, plus de tentative disponible")
                answer = (
                    "Je n'ai pas pu obtenir une réponse fiable pour cette question. "
                    "Pouvez-vous la reformuler ou la poser à nouveau ?"
                )
                print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
                return answer

            print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
            return content

        if len(tool_calls) > MAX_TOOL_CALLS_PER_REQUEST:
            print(
                "   [orchestrateur] Limite d'appels d'outils dépassée "
                f"({len(tool_calls)} > {MAX_TOOL_CALLS_PER_REQUEST})"
            )
            print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
            return "Je n'ai pas pu traiter cette demande de façon fiable. Pouvez-vous la reformuler plus précisément ?"

        messages.append(message)
        executed_results = []
        report_requested = _is_report_request(user_question)
        producer_calls = [
            call for call in tool_calls
            if call["function"]["name"] in DATA_AGENT_NAMES
        ]
        report_calls = [
            call for call in tool_calls
            if call["function"]["name"] == "report_agent"
        ]

        if report_requested and not producer_calls:
            inferred_agent, inferred_input = _infer_data_agent_for_report(user_question)
            producer_calls = [{"function": {"name": inferred_agent, "arguments": inferred_input}}]
            print(
                "   [orchestrateur] report_agent différé : "
                f"source de données inférée = {inferred_agent}"
            )

        if report_requested:
            calls_to_execute = producer_calls
            if report_calls:
                print("   [orchestrateur] report_agent différé jusqu'à la collecte des données")
        else:
            calls_to_execute = tool_calls

        for call in calls_to_execute:
            agent_name = call["function"]["name"]
            agent_input = call["function"]["arguments"]
            print(f"-> Le modèle choisit l'agent : {agent_name} avec {agent_input}")

            if agent_name not in agent_functions:
                result = {"error": "Agent demandé non disponible."}
                executed_results.append((agent_name, result))
                continue

            function = agent_functions[agent_name]


            sig = inspect.signature(function)
            expected_params = set(sig.parameters.keys())
            filtered_input = {k: v for k, v in agent_input.items() if k in expected_params}
            ignored = set(agent_input.keys()) - expected_params
            if ignored:
                print(f"   [orchestrateur] Paramètres ignorés (non prévus par {agent_name}) : {ignored}")


            required_params = {
                name for name, param in sig.parameters.items()
                if param.default is inspect.Parameter.empty
            }
            missing = required_params - set(filtered_input.keys())

            if missing:
                print(f"   [orchestrateur] Appel invalide : paramètre(s) manquant(s) {missing} pour {agent_name}")
                result = {
                    "error": (
                        f"Appel invalide à {agent_name} : paramètre(s) requis manquant(s) {missing}. "
                        f"L'agent n'a pas été exécuté."
                    )
                }
            else:
                agent_started_at = perf_counter()
                result = function(**filtered_input)
                if agent_name != "sql_agent":
                    print(f"[PERF] {agent_name} = {perf_counter() - agent_started_at:.2f}s")


                if agent_name != "report_agent":
                    collected_results.append((agent_name, filtered_input, result))

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

            executed_results.append((agent_name, result))

        if not _is_report_request(user_question):
            answer = _format_agent_results(executed_results, user_question)
            print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
            return answer

        real_results_text = _format_collected_results(collected_results)
        if not real_results_text:
            print("   [orchestrateur] Rapport non exécuté : aucune source de données exploitable")
            print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
            return NON_MEASURABLE_QUESTION_MESSAGE

        print("   [orchestrateur] Exécution différée de report_agent après les agents producteurs")
        report_started_at = perf_counter()
        report_result = report_agent(real_results_text)
        print(f"[PERF] report_agent = {perf_counter() - report_started_at:.2f}s")
        answer = _format_agent_result("report_agent", report_result, user_question)
        print(f"[PERF] total = {perf_counter() - total_started_at:.2f}s")
        return answer


if __name__ == "__main__":
    questions = [
        "Quel est le produit le plus vendu ?",
        "Quelles seront nos ventes le mois prochain en Technology ?",
        "Fais-moi un rapport sur le produit qui s'est le plus vendu au total.",
        "Quelle est la marge sur la catégorie Furniture ?",
        "Fais-moi un résumé de la marge sur la catégorie Furniture.",
        "Donne-moi un rapport sur la croissance des ventes en 2013.",
        "Quelles sont les 3 régions avec le plus de profit ?",
    ]
    for q in questions:
        answer = ask_orchestrator(q)
        print(f"\nRéponse finale de l'orchestrateur :\n{answer}\n")
        print("=" * 60)
