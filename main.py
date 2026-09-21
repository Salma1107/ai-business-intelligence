import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

df=pd.read_csv('data/raw/superstore.csv', encoding="utf-8")

df = df.drop(columns=["记录数"])

df =df.rename(columns={
    "Category":"category",
    "City":"city",
    "Country":"country",
    "Customer.ID": "customer_id",
    "Customer.Name": "customer_name",
    "Discount": "discount",
    "Market": "market",
    "Order.Date": "order_date",
    "Order.ID": "order_id",
    "Order.Priority": "order_priority",
    "Product.ID": "product_id",
    "Product.Name": "product_name",
    "Profit": "profit",
    "Quantity": "quantity",
    "Region": "region",
    "Row.ID": "row_id",
    "Sales": "sales",
    "Segment": "segment",
    "Ship.Date": "ship_date",
    "Ship.Mode": "ship_mode",
    "Shipping.Cost": "shipping_cost",
    "State": "state",
    "Sub.Category": "sub_category",
    "Year": "year",
    "Market2": "market2",
    "weeknum": "weeknum",
})

df["order_date"] = pd.to_datetime(df["order_date"])
df["ship_date"] =  pd.to_datetime(df["ship_date"])

print(df[["sales", "profit", "discount", "shipping_cost", "quantity"]].dtypes)

print("Doublons:", df.duplicated().sum())
print("Valeurs manquantes: \n", df.isna().sum()[df.isna().sum()>0])

df.to_csv("data/processed/superstore.csv", index=False)
print("Nettoyage terminé:", df.shape)





