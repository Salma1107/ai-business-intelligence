import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("superstore_clean.csv", encoding="utf-8", parse_dates=["order_date"])
print("Dimensions :", df.shape)

daily_sales = df.groupby("order_date")["sales"].sum().reset_index()
daily_sales.columns = ["date", "sales"]

daily_sales = (
    daily_sales.set_index("date")
    .asfreq("D", fill_value=0)
    .reset_index()
)

print("Nombre de jours :", len(daily_sales))
print("Jours sans aucune vente :", (daily_sales["sales"] == 0).sum())
daily_sales.head()


