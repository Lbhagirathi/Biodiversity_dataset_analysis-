import pandas as pd

# =========================
# LOAD DATA
# =========================
df = pd.read_parquet(
    "data/grid_assigned.parquet",
    columns=["species"]
)

# =========================
# COUNT SPECIES OCCURRENCES
# =========================
abundance = df["species"].value_counts().reset_index()

# Rename columns
abundance.columns = ["species", "abundance"]

# =========================
# SORT BY ABUNDANCE
# =========================
abundance = abundance.sort_values(
    by="abundance",
    ascending=False
)

# =========================
# SAVE
# =========================
abundance.to_csv(
    "results/tables/species_abundance.csv",
    index=False
)

print("✅ Species abundance table saved!")

print("\nTop 10 most abundant species:")
print(abundance.head(10))