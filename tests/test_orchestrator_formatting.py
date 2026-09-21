from unittest.mock import patch

import Orchestrator


def test_format_sql_result_with_single_top_product():
    result = {"rows": [{"product_name": "Staples", "total_sales": 876}]}

    assert Orchestrator._format_sql_result(result, "Quel produit est le plus vendu ?") == (
        "Le produit le plus vendu est Staples, avec 876 unités vendues."
    )


def test_format_sql_result_with_multiple_rows():
    result = {
        "rows": [
            {"region": "Central", "total_profit": 311403.75},
            {"region": "North", "total_profit": 194597.41},
        ]
    }

    assert Orchestrator._format_sql_result(result, "Quelles régions ont le plus de profit ?") == (
        "Résultats :\n1. Central : 311 403,75\n2. North : 194 597,41"
    )


def test_format_sql_result_with_no_rows():
    assert Orchestrator._format_sql_result({"rows": []}, "Produits en 2099") == (
        "Aucun résultat n’a été trouvé pour cette question."
    )


def test_format_analytics_result():
    answer = Orchestrator._format_agent_result(
        "analytics_agent", {"kpi": "marge", "value_pct": 13.99}, "Quelle marge ?"
    )

    assert answer == "Marge : 13,99 %."


def test_format_forecast_result():
    answer = Orchestrator._format_agent_result(
        "forecast_agent", {"prediction": 152000, "horizon_days": 30}, "Prévision"
    )

    assert answer == "Prévision : 152 000. Horizon : 30 jours."


def test_report_request_defers_report_until_sql_data_is_collected():
    events = []

    def fake_sql_agent(question):
        events.append(("sql_agent", question))
        return {"rows": [{"product_name": "Staples", "total_sales": 876}]}

    def fake_report_agent(results):
        events.append(("report_agent", results))
        return {"title": "Produit leader", "summary": "Staples est le produit le plus vendu.", "key_points": []}

    with (
        patch.object(Orchestrator.ollama, "chat") as routing_chat,
        patch.dict(
            Orchestrator.agent_functions,
            {"sql_agent": fake_sql_agent, "report_agent": fake_report_agent},
        ),
        patch.object(Orchestrator, "report_agent", fake_report_agent),
    ):
        answer = Orchestrator.ask_orchestrator("Fais-moi un rapport sur le produit le plus vendu.")

    assert answer == "Staples est le produit le plus vendu."
    assert events[0][0] == "sql_agent"
    assert events[1][0] == "report_agent"
    assert "Staples" in events[1][1]
    routing_chat.assert_not_called()


def test_report_request_uses_analytics_before_report():
    events = []

    def fake_analytics_agent(metric, context=""):
        events.append(("analytics_agent", metric, context))
        return {"kpi": "marge", "value_pct": 6.94}

    def fake_report_agent(results):
        events.append(("report_agent", results))
        return {"title": "Marge", "summary": "La marge est de 6,94 %.", "key_points": []}

    with (
        patch.object(Orchestrator.ollama, "chat") as routing_chat,
        patch.dict(
            Orchestrator.agent_functions,
            {"analytics_agent": fake_analytics_agent, "report_agent": fake_report_agent},
        ),
        patch.object(Orchestrator, "report_agent", fake_report_agent),
    ):
        answer = Orchestrator.ask_orchestrator("Donne-moi un résumé de la marge sur la catégorie Furniture.")

    assert answer == "La marge est de 6,94 %."
    assert events[0][0] == "analytics_agent"
    assert events[1][0] == "report_agent"
    routing_chat.assert_not_called()


def test_non_measurable_question_does_not_call_an_agent():
    with patch.object(Orchestrator.ollama, "chat") as chat:
        answer = Orchestrator.ask_orchestrator("Comment améliorer les ventes ?")

    assert answer == Orchestrator.NON_MEASURABLE_QUESTION_MESSAGE
    chat.assert_not_called()
