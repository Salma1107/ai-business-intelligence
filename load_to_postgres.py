import pandas as pd
from db_connection import engine


dim_product = pd.read_csv("dim_product.csv")
dim_customer = pd.read_csv("dim_customer.csv")
dim_geography = pd.read_csv("dim_geography.csv")
dim_time = pd.read_csv("dim_time.csv")
fact_sales = pd.read_csv("fact_sales.csv")

print("Insertion dim_product:")
dim_product.to_sql("dim_product", engine, if_exists="append", index=False)

print("Insertion dim_customer:")
dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)

print("Insertion dim_geography:")
dim_geography.to_sql("dim_geography", engine, if_exists="append", index=False)

print("Insertion dim_time:")
dim_time.to_sql("dim_time", engine, if_exists="append", index=False)

print("Insertion fact_sales:")
fact_sales.to_sql("fact_sales", engine, if_exists="append", index=False)

print("\nChargement terminé avec succès.")

with engine.connect() as conn:
    from sqlalchemy import text
    for table in [
        "dim_product",
        "dim_customer",
        "dim_geography",
        "dim_time",
        "fact_sales"
    ]:
        count = conn.execute(text(f"select count(*) from {table}")).scalar()
        print(f"{table} : {count} lignes en base")
