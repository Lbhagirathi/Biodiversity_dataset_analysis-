import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_parquet(
    "data/admin_assigned.parquet",
    columns=["species","grid_cell_id","admin_region"]
)

grid_richness = df.groupby("grid_cell_id")["species"].nunique()
grid_admin = df.groupby("grid_cell_id")["admin_region"].first()

grid_df = pd.DataFrame({
    "richness": grid_richness,
    "admin_region": grid_admin
})

# Remove extremely low richness grids
grid_df = grid_df[grid_df["richness"] > 20]

plt.figure(figsize=(8,5))

grid_df.boxplot(
    column="richness",
    by="admin_region",
    grid=False
)

plt.title("Distribution of Grid Biodiversity within Regions")
plt.suptitle("")

plt.xlabel("Administrative Region")
plt.ylabel("Species per Grid Cell")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig("results/plots/grid_distribution_by_region.png", dpi=300)
plt.close()