import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 5)


df = pd.read_csv("data/processed/superstore_clean.csv", encoding="utf-8", parse_dates=["order_date", "ship_date"])
print("Dimensions :", df.shape)
print(df.head())

print(df.info())


print("Doublons :", df.duplicated().sum())
print("\nValeurs manquantes :")
print(df.isna().sum()[df.isna().sum() > 0] if df.isna().sum().sum() > 0 else "Aucune")


#2.Analyse univariée

fig, axes = plt.subplots(2, 2, figsize=(14, 8))
sns.histplot(df["sales"], bins=50, ax=axes[0,0], color="#2E74B5").set_title("Distribution des ventes (Sales)")
sns.histplot(df["profit"], bins=50, ax=axes[0,1], color="#1E8A5A").set_title("Distribution du profit (Profit)")
sns.histplot(df["discount"], bins=20, ax=axes[1,0], color="#B8860B").set_title("Distribution de la remise (Discount)")
sns.histplot(df["quantity"], bins=14, ax=axes[1,1], color="#8A2BE2").set_title("Distribution de la quantité (Quantity)")
plt.tight_layout()
plt.show()


fig, axes = plt.subplots(1, 3, figsize=(16, 5))
df["category"].value_counts().plot(kind="bar", ax=axes[0], color="#2E74B5", title="Nombre de ventes par catégorie")
df["segment"].value_counts().plot(kind="bar", ax=axes[1], color="#1E8A5A", title="Nombre de ventes par segment client")
df["market"].value_counts().plot(kind="bar", ax=axes[2], color="#B8860B", title="Nombre de ventes par marché")
for ax in axes:
    ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.show()



#3.Analyse bivariée

plt.figure(figsize=(8,6))
sns.scatterplot(data=df.sample(3000, random_state=42), x="discount", y="profit", alpha=0.4, color="#2E74B5")
plt.axhline(0, color="red", linestyle="--", linewidth=1)
plt.title("Profit en fonction de la remise (Discount)")
plt.show()

cat_summary = df.groupby("category")[["sales","profit"]].sum().sort_values("profit", ascending=False)
cat_summary["margin_pct"] = (cat_summary["profit"] / cat_summary["sales"] * 100).round(1)
print(cat_summary)

cat_summary[["sales","profit"]].plot(kind="bar", figsize=(8,5), color=["#2E74B5","#1E8A5A"])
plt.title("Ventes et profit total par catégorie")
plt.ylabel("Montant ($)")
plt.show()


numeric_cols = ["sales","profit","discount","quantity","shipping_cost"]
corr = df[numeric_cols].corr()
plt.figure(figsize=(7,6))
sns.heatmap(corr, annot=True, cmap="RdBu_r", center=0, fmt=".2f")
plt.title("Matrice de corrélation")
plt.show()


#4.Analyse temporelle

monthly = df.set_index("order_date").resample("ME")["sales"].sum()
plt.figure(figsize=(12,5))
monthly.plot(color="#2E74B5")
plt.title("Évolution mensuelle des ventes (2011-2014)")
plt.ylabel("Ventes ($)")
plt.show()


df["day_of_week"] = df["order_date"].dt.day_name()
order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow_sales = df.groupby("day_of_week")["sales"].sum().reindex(order)
dow_sales.plot(kind="bar", figsize=(8,5), color="#B8860B")
plt.title("Ventes totales par jour de la semaine")
plt.ylabel("Ventes ($)")
plt.show()

yearly = df.groupby(df["order_date"].dt.year)["sales"].sum()
growth = yearly.pct_change().round(3) * 100
print("Ventes par année :\n", yearly)
print("\nCroissance annuelle (%) :\n", growth)



