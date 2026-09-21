from unittest.mock import patch

import pandas as pd

import sql_agent


def test_sql_agent_generates_executes_and_returns_rows():
    generated_sql = "SELECT product_name FROM dim_product"
    returned_rows = [{"product_name": "Staples"}]

    with (
        patch.object(sql_agent, "generate_sql", return_value=generated_sql),
        patch.object(sql_agent, "execute_sql", return_value=returned_rows) as execute,
    ):
        result = sql_agent.sql_agent("Quel produit est le plus vendu ?")

    assert result["rows"] == returned_rows
    assert result["sql_used"] == "SELECT product_name FROM dim_product LIMIT 1;"
    execute.assert_called_once_with("SELECT product_name FROM dim_product LIMIT 1;")


def test_execute_sql_converts_dataframe_to_rows():
    dataframe = pd.DataFrame(
        [
            {"product_name": "Staples", "total_sales": 876},
            {"product_name": "Paper", "total_sales": 500},
        ]
    )

    with patch.object(sql_agent.pd, "read_sql", return_value=dataframe):
        rows = sql_agent.execute_sql("SELECT product_name, total_sales FROM sales;")

    assert rows == dataframe.to_dict(orient="records")


def test_sql_agent_returns_error_when_execution_fails():
    with (
        patch.object(sql_agent, "generate_sql", return_value="SELECT * FROM fact_sales;"),
        patch.object(sql_agent, "execute_sql", side_effect=RuntimeError("base indisponible")),
    ):
        result = sql_agent.sql_agent("Liste les ventes")

    assert result == {"error": sql_agent.USER_SQL_ERROR_MESSAGE}


def test_validate_sql_rejects_a_hallucinated_table():
    is_safe, reason = sql_agent.validate_sql(
        "SELECT * FROM fact_sales f JOIN dim_ship_mode sm ON f.ship_mode = sm.ship_mode;"
    )

    assert not is_safe
    assert reason == "Table inconnue détectée : dim_ship_mode"


def test_sql_agent_hides_technical_details_when_a_table_is_invalid():
    with patch.object(
        sql_agent,
        "generate_sql",
        return_value="SELECT * FROM dim_order_priority;",
    ) as generate:
        result = sql_agent.sql_agent("Comment améliorer les ventes ?")

    assert result == {"error": sql_agent.USER_SQL_ERROR_MESSAGE}
    generate.assert_called_once()
