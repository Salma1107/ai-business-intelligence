import re
import numpy as np
import pandas as pd
import joblib
from tensorflow import keras

from backend.core.config import MODEL_DIR
from db_connection import engine

model_path = MODEL_DIR / "lstm_sales_forecast.keras"
scaler_path = MODEL_DIR / "sales_scaler.joblib"
features_path = MODEL_DIR / "feature_columns.joblib"

_model = keras.models.load_model(model_path)
_scaler = joblib.load(scaler_path)
_feature_cols = joblib.load(features_path)

window = 14

_categories_shares = {
    "technology": 0.3753,
    "office supplies": 0.2996,
    "furniture": 0.3252,
}

def _fetch_recent_daily_sales(n_days: int = 60) -> pd.DataFrame:
    sql = f""" SELECT t.full_date AS date, SUM(f.sales) AS sales FROM fact_sales f JOIN dim_time t ON f.order_date_id = t.date_id GROUP BY t.full_date ORDER BY t.full_date DESC LIMIT {n_days + window + 30}; """

    df = pd.read_sql(sql, engine)
    df = df.sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    full_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_range, fill_value=0).reset_index()
    df.columns = ["date", "sales"]
    return df


def _build_features(hist_df: pd.DataFrame) -> pd.DataFrame:
    d = hist_df.copy()
    d["month"] = d["date"].dt.month
    d["day_of_week"] = d["date"].dt.dayofweek
    d["quarter"] = d["date"].dt.quarter
    d["is_year_end"] = d["month"].isin([11, 12]).astype(int)
    d["sales_lag_1"] = d["sales"].shift(1)
    d["sales_lag_7"] = d["sales"].shift(7)
    d["sales_lag_14"] = d["sales"].shift(14)
    d["sales_lag_30"] = d["sales"].shift(30)
    d["sales_rolling_7"] = d["sales"].rolling(7).mean()
    d["sales_rolling_30"] = d["sales"].rolling(30).mean()
    return d


def _predict_next_day(hist_df: pd.DataFrame) -> float:
    feat = _build_features(hist_df).dropna().reset_index(drop=True)
    window_df = feat[_feature_cols].tail(window)
    scaled = _scaler.transform(window_df)
    X = scaled.reshape(1, window, len(_feature_cols))
    pred_scaled = _model.predict(X, verbose=0)[0][0]
    dummy = np.zeros((1, len(_feature_cols)))
    dummy[0, 0] = pred_scaled
    pred_real = _scaler.inverse_transform(dummy)[0, 0]

    return max(float(pred_real), 0.0)


def _recursive_forecast(hist_df: pd.DataFrame, n_days: int) -> list:
    working = hist_df[["date", "sales"]].copy()
    predictions = []
    last_date = working["date"].max()

    for i in range(n_days):
        next_pred = _predict_next_day(working)
        next_date = last_date + pd.Timedelta(days=i + 1)
        working = pd.concat(
            [working, pd.DataFrame({"date": [next_date], "sales": [next_pred]})],
            ignore_index=True,
        )
        predictions.append(next_pred)

    return predictions


def _parse_horizon_to_days(horizon: str) -> int:
    horizon = horizon.lower()
    match = re.search(r"(\d+)", horizon)
    number = int(match.group(1)) if match else 1

    if "mois" in horizon:
        return number * 30
    if "semaine" in horizon:
        return number * 7
    if "jour" in horizon:
        return number
    return 30


def forecast_agent(horizon: str, segment: str = "") -> dict:
    print(f"   [forecast_agent] Horizon : {horizon} , segment : {segment}")

    n_days = _parse_horizon_to_days(horizon)

    try:
        history = _fetch_recent_daily_sales()
    except Exception as e:
        print(f"   [forecast_agent] Erreur de récupération des données : {e}")
        return {"error": f"Impossible de récupérer l'historique des ventes : {e}"}

    daily_predictions = _recursive_forecast(history, n_days)
    total_prediction = sum(daily_predictions)

    note = None
    segment_clean = segment.lower().strip()
    for category, share in _categories_shares.items():
        if category in segment_clean:
            total_prediction *= share
            note = (
                f"Prévision approximée pour la catégorie '{category}' à partir de sa part "
                f"historique moyenne ({share * 100:.1f}%) dans les ventes totales — le modèle "
                f"n'est pas entraîné séparément par catégorie."
            )
            break

    reference_daily_mae = 4850
    uncertainty = reference_daily_mae * (n_days ** 0.5)  # croît avec la racine du nb de jours

    result = {
        "prediction": round(total_prediction, 2),
        "confidence_interval": [
            round(max(total_prediction - uncertainty, 0), 2),
            round(total_prediction + uncertainty, 2),
        ],
        "horizon_days": n_days,
    }
    if note:
        result["note"] = note

    print(f"   [forecast_agent] Résultat : {result}")
    return result


if __name__ == "__main__":
    tests = [
        ("1 mois", ""),
        ("1 semaine", "Technology"),
        ("7 jours", ""),
    ]
    for horizon, segment in tests:
        print("\n" + "=" * 60)
        result = forecast_agent(horizon, segment)
        print(result)
