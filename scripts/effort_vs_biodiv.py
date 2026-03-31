import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_parquet(
    "data/grid_assigned.parquet",
    columns=["species","grid_cell_id","eventDate","recordedBy"]
)

df["event_id"] = df["recordedBy"].astype(str) + df["eventDate"].astype(str)

richness = df.groupby("grid_cell_id")["species"].nunique()
effort = df.groupby("grid_cell_id")["event_id"].nunique()

summary = pd.DataFrame({
    "richness": richness,
    "effort": effort
})

plt.figure(figsize=(6,6))

plt.scatter(
    summary["effort"],
    summary["richness"],
    s=8,
    alpha=0.6
)

plt.xlabel("Sampling Effort")
plt.ylabel("Species Richness")
plt.title("Sampling Bias in Biodiversity Data")

plt.savefig("results/plots/effort_vs_richness.png", dpi=300)
plt.close()