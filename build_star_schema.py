import pandas as pd

df = pd.read_csv("../data/raw/superstore.csv", encoding="utf-8")

df = df.drop(columns=["记录数"])

df = df.rename(columns={
    "Category": "category", "City": "city", "Country": "country",
    "Customer.ID": "customer_id", "Customer.Name": "customer_name",
    "Discount": "discount", "Market": "market",
    "Order.Date": "order_date", "Order.ID": "order_id",
    "Order.Priority": "order_priority", "Product.ID": "product_id",
    "Product.Name": "product_name", "Profit": "profit",
    "Quantity": "quantity", "Region": "region", "Row.ID": "row_id",
    "Sales": "sales", "Segment": "segment", "Ship.Date": "ship_date",
    "Ship.Mode": "ship_mode", "Shipping.Cost": "shipping_cost",
    "State": "state", "Sub.Category": "sub_category", "Year": "year",
    "Market2": "market2", "weeknum": "weeknum",
})

df["order_date"] = pd.to_datetime(df["order_date"])
df["ship_date"] = pd.to_datetime(df["ship_date"])

dim_product = (
    df[["product_id", "product_name", "category", "sub_category"]].drop_duplicates().reset_index(drop=True)
)

dim_product.insert(0, "product_key", range(1, len(dim_product)+1))

dim_customer= (
    df[["customer_id", "customer_name", "segment"]]
    .drop_duplicates(subset="customer_id").reset_index(drop=True)
)


dim_geography = (
    df[["city", "state", "country","region", "market", "market2"]].drop_duplicates().reset_index(drop=True)
)

dim_geography.insert(0, "geography_id", range(1, len(dim_geography)+1))

all_dates = (
    pd.concat([df["order_date"], df["ship_date"]]).drop_duplicates().sort_values().reset_index(drop=True)
)

dim_time = pd.DataFrame({"full_date": all_dates})
dim_time.insert(0, "date_id", range(1, len(dim_time)+1))
dim_time["year"] = dim_time["full_date"].dt.year
dim_time["month"] = dim_time["full_date"].dt.month
dim_time["day"] = dim_time["full_date"].dt.day
dim_time["weeknum"] = dim_time["full_date"].dt.isocalendar().week
dim_time["day_of_week"] = dim_time["full_date"].dt.day_name()
dim_time["quarter"] = dim_time["full_date"].dt.quarter

fact_sales = df.merge(
    dim_product, on=["product_id", "product_name", "category", "sub_category"], how = "left"
)

fact_sales = fact_sales.merge(
    dim_customer, on=["customer_id", "customer_name", "segment"], how = "left"
)

fact_sales = fact_sales.merge(
    dim_geography, on=["city", "state", "country", "region", "market", "market2"], how = "left"
)

fact_sales = fact_sales.merge(
    dim_time[["date_id", "full_date"]], left_on="order_date", right_on="full_date", how="left"
).rename(columns={"date_id":"order_date_id"}).drop(columns=["full_date"])

fact_sales = fact_sales.merge(
    dim_time[["date_id", "full_date"]], left_on="ship_date", right_on="full_date", how="left"
).rename(columns={"date_id":"ship_date_id"}).drop(columns=["full_date"])

fact_sales = fact_sales[[
    "order_id", "product_key", "customer_id", "geography_id",
    "order_date_id", "ship_date_id", "order_priority", "ship_mode",
    "sales", "profit", "quantity", "discount", "shipping_cost",
]]

key_columns = ["product_key", "customer_id", "geography_id", "order_date_id", "ship_date_id"]
missing_keys = fact_sales[key_columns].isna().sum().sum()

print("Clés manquantes dans fact_sales:", missing_keys)

dim_product.to_csv("dim_product.csv", index=False)
dim_customer.to_csv("dim_customer.csv", index=False)
dim_geography.to_csv("dim_geography.csv", index=False)
dim_time.to_csv("dim_time.csv", index=False)
fact_sales.to_csv("fact_sales.csv", index=False)

print("\nRécapitulatif :")
print("dim_product   :", dim_product.shape)
print("dim_customer  :", dim_customer.shape)
print("dim_geography :", dim_geography.shape)
print("dim_time      :", dim_time.shape)
print("fact_sales    :", fact_sales.shape)
