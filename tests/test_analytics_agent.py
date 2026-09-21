from unittest.mock import patch

import pandas as pd

import analytics_agent


def test_build_where_clause_keeps_only_supported_filters():
    where = analytics_agent._build_where_clause(
        {"category": "Technology", "year": 2013, "region": "Central"}
    )

    assert where == "WHERE p.category = 'Technology' AND t.year = 2013"


def test_build_where_clause_returns_empty_for_invalid_filters():
    assert analytics_agent._build_where_clause({"category": "Unknown", "year": 2099}) == ""


def test_kpi_marge_uses_simulated_dataframe():
    dataframe = pd.DataFrame([{"total_profit": 50.0, "total_sales": 200.0}])

    with patch.object(analytics_agent.pd, "read_sql", return_value=dataframe):
        result = analytics_agent.kpi_marge({"category": "Technology"})

    assert result == {
        "kpi": "marge",
        "value_pct": 25.0,
        "filters_applied": {"category": "Technology"},
    }


def test_analytics_agent_returns_error_for_unknown_kpi():
    with patch.object(analytics_agent, "classify_request", return_value={"kpi": "inconnu", "filters": {}}):
        result = analytics_agent.analytics_agent("indicateur inconnu")

    assert "error" in result
    assert "Aucun KPI reconnu" in result["error"]
