from unittest.mock import patch

import pandas as pd

import forecast_agent


def test_parse_horizon_to_days():
    assert forecast_agent._parse_horizon_to_days("2 mois") == 60
    assert forecast_agent._parse_horizon_to_days("3 semaines") == 21
    assert forecast_agent._parse_horizon_to_days("7 jours") == 7
    assert forecast_agent._parse_horizon_to_days("prochain") == 30


def test_build_features_adds_expected_columns():
    history = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=35, freq="D"),
            "sales": list(range(35)),
        }
    )

    features = forecast_agent._build_features(history)

    assert {"month", "day_of_week", "quarter", "sales_lag_30", "sales_rolling_30"}.issubset(
        features.columns
    )
    assert features.loc[30, "sales_lag_30"] == 0


def test_forecast_agent_applies_technology_share_without_model_or_database():
    history = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "sales": [100.0]})

    with (
        patch.object(forecast_agent, "_fetch_recent_daily_sales", return_value=history),
        patch.object(forecast_agent, "_recursive_forecast", return_value=[100.0]),
    ):
        result = forecast_agent.forecast_agent("1 jour", "Technology")

    assert result["prediction"] == 37.53
    assert result["horizon_days"] == 1
    assert "part historique moyenne" in result["note"]
