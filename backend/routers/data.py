from fastapi import APIRouter, Depends
import pandas as pd

from backend.core.deps import get_current_user_email
from db_connection import engine

router = APIRouter(prefix="/data", tags=["Données (dashboard)"])


@router.get("/categories")
def get_categories(user_email: str = Depends(get_current_user_email)):
    df = pd.read_sql("SELECT DISTINCT category FROM dim_product ORDER BY category;", engine)
    return {"categories": df["category"].tolist()}

@router.get("/regions")
def get_regions(user_email: str = Depends(get_current_user_email)):
    df = pd.read_sql("SELECT DISTINCT region FROM dim_geography ORDER BY region;", engine)
    return {"regions": df["region"].tolist()}


@router.get("/kpis/summary")
def get_kpi_summary(user_email: str = Depends(get_current_user_email)):
    sql = """
        SELECT
            SUM(sales) AS total_sales,
            SUM(profit) AS total_profit,
            COUNT(DISTINCT order_id) AS total_orders
        FROM fact_sales;
    """
    row = pd.read_sql(sql, engine).iloc[0]
    total_sales = float(row["total_sales"])
    total_profit = float(row["total_profit"])

    return {
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "margin_pct": round(total_profit / total_sales * 100, 2) if total_sales else None,
        "total_orders": int(row["total_orders"]),
    }


@router.get("/sales/timeseries")
def get_sales_timeseries(user_email: str = Depends(get_current_user_email)):
    sql = """
        SELECT t.year, t.month, SUM(f.sales) AS total_sales
        FROM fact_sales f
        JOIN dim_time t ON f.order_date_id = t.date_id
        GROUP BY t.year, t.month
        ORDER BY t.year, t.month;
    """
    df = pd.read_sql(sql, engine)
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    return {
        "series": df[["period", "total_sales"]].to_dict(orient="records")
    }