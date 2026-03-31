import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_parquet(
    "data/admin_assigned.parquet",
    columns=[
        "species",
        "grid_cell_id",
        "admin_region"
    ]
)

# -------------------------
# GRID LEVEL RICHNESS
# -------------------------
grid_richness = df.groupby("grid_cell_id")["species"].nunique()

# attach admin region to each grid
grid_admin = df.groupby("grid_cell_id")["admin_region"].first()

grid_summary = pd.DataFrame({
    "grid_richness": grid_richness,
    "admin_region": grid_admin
})

# -------------------------
# ADMIN REGION RICHNESS
# -------------------------
admin_richness = df.groupby("admin_region")["species"].nunique()

# mean grid richness per admin region
mean_grid_richness = grid_summary.groupby("admin_region")["grid_richness"].mean()

comparison = pd.DataFrame({
    "admin_total_richness": admin_richness,
    "mean_grid_richness": mean_grid_richness
})

print(comparison)

# -------------------------
# PLOT COMPARISON
# -------------------------
plt.figure(figsize=(8,5))

plt.bar(comparison.index, comparison["admin_total_richness"], alpha=0.6, label="Admin Region Richness")

plt.plot(comparison.index, comparison["mean_grid_richness"], marker="o", linewidth=2, label="Mean Grid Richness")

plt.ylabel("Species Richness")
plt.title("Grid vs Administrative Region Biodiversity Estimates")

plt.xticks(rotation=45)

plt.legend()

plt.tight_layout()

plt.savefig("results/plots/grid_vs_admin_comparison.png", dpi=300)

plt.close()