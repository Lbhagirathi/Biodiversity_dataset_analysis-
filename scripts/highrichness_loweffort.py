import pandas as pd

# Load data
df = pd.read_parquet(
    "data/grid_assigned.parquet",
    columns=[
        "species",
        "grid_cell_id",
        "lat_bin",
        "lon_bin",
        "eventDate",
        "recordedBy"
    ]
)

# -------------------------
# Species richness
# -------------------------
richness = df.groupby("grid_cell_id")["species"].nunique()

# -------------------------
# Sampling effort
# -------------------------
df["event_id"] = df["recordedBy"].astype(str) + "_" + df["eventDate"].astype(str)

effort = df.groupby("grid_cell_id")["event_id"].nunique()

# -------------------------
# Coordinates
# -------------------------
coords = df.groupby("grid_cell_id")[["lat_bin","lon_bin"]].first()

# -------------------------
# Combine metrics
# -------------------------
summary = pd.concat([richness, effort, coords], axis=1)
summary.columns = ["richness","effort","lat_bin","lon_bin"]

# -------------------------
# Define thresholds
# -------------------------
rich_threshold = summary["richness"].quantile(0.60)
effort_threshold = summary["effort"].quantile(0.40)

print("Richness threshold:", rich_threshold)
print("Effort threshold:", effort_threshold)

# -------------------------
# Identify under-sampled biodiversity areas
# -------------------------
targets = summary[
    (summary["richness"] >= rich_threshold) &
    (summary["effort"] <= effort_threshold)
]

# -------------------------
# Save results
# -------------------------
targets.to_csv(
    "results/tables/high_richness_low_effort.csv"
)

print("\nPotential under-sampled biodiversity regions:")
print(targets)

print("\nTotal target cells:", len(targets))