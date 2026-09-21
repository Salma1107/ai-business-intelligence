from unittest.mock import patch

import report_agent


def test_report_agent_refuses_insufficient_data():
    with patch.object(report_agent.ollama, "chat") as chat:
        result = report_agent.report_agent("Aucune donnée exploitable")

    assert "error" in result
    chat.assert_not_called()


def test_report_agent_returns_valid_json_from_ollama():
    ollama_response = {
        "message": {
            "content": (
                '{"title":"Ventes",'
                '"summary":"Les ventes totalisent 876 unités.",'
                '"key_points":["Staples est en tête."]}'
            )
        }
    }

    with patch.object(report_agent.ollama, "chat", return_value=ollama_response) as chat:
        result = report_agent.report_agent("Produit le plus vendu : Staples, quantité totale : 876 unités.")

    assert result == {
        "title": "Ventes",
        "summary": "Les ventes totalisent 876 unités.",
        "key_points": ["Staples est en tête."],
    }
    chat.assert_called_once()


def test_report_agent_uses_text_fallback_when_ollama_returns_invalid_json():
    ollama_response = {"message": {"content": "Les ventes totalisent 876 unités."}}

    with patch.object(report_agent.ollama, "chat", return_value=ollama_response):
        result = report_agent.report_agent("Produit le plus vendu : Staples, quantité totale : 876 unités.")

    assert result == {
        "title": "Rapport",
        "summary": "Les ventes totalisent 876 unités.",
        "key_points": [],
    }


def test_metric_semantics_distinguishes_sales_from_quantity():
    sales_guidance = report_agent._metric_semantics_guidance(
        '{"product_name": "Phone", "total_sales": 86936}'
    )
    quantity_guidance = report_agent._metric_semantics_guidance(
        '{"product_name": "Staples", "total_quantity": 876}'
    )

    assert "montant des ventes" in sales_guidance
    assert "jamais une quantité" in sales_guidance
    assert "unités vendues" in quantity_guidance


def test_report_prompt_forbids_unsupported_comparisons():
    assert "Utilise exclusivement les faits et mesures présents" in report_agent.SYSTEM_PROMPT
    assert "supérieure, inférieure, meilleure, pire" in report_agent.SYSTEM_PROMPT
    assert "valeurs de comparaison nécessaires" in report_agent.SYSTEM_PROMPT
