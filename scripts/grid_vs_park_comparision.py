import pandas as pd
import matplotlib.pyplot as plt

# Load data
grid = pd.read_csv("results/tables/biodiversity_hotspots.csv")
parks = pd.read_csv("results/tables/park_biodiversity_summary.csv")

plt.figure(figsize=(6,6))

# Grid hotspots
plt.scatter(
    grid["richness"],
    [1]*len(grid),
    label="Grid hotspots",
    alpha=0.6
)

# Parks
plt.scatter(
    parks["species_richness"],
    [2]*len(parks),
    label="Parks",
    s=80
)

plt.yticks([1,2], ["Grid Cells", "Parks"])
plt.xlabel("Species Richness")

plt.title("Grid vs Park Biodiversity Comparison")

plt.legend()

plt.savefig("results/plots/grid_vs_park_comparison.png", dpi=300)
plt.close()