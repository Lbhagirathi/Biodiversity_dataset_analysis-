import pandas as pd

df = pd.read_parquet(
    "data/grid_assigned.parquet",
    columns=[
        "species",
        "grid_cell_id",
        "eventDate",
        "recordedBy"
    ]
)

richness = df.groupby("grid_cell_id")["species"].nunique()

df["event_id"] = df["recordedBy"].astype(str) + df["eventDate"].astype(str)
effort = df.groupby("grid_cell_id")["event_id"].nunique()

summary = pd.DataFrame({
    "richness": richness,
    "effort": effort
})

# Define thresholds
rich_threshold = summary["richness"].quantile(0.85)
effort_threshold = summary["effort"].quantile(0.25)

targets = summary[
    (summary["richness"] >= rich_threshold) &
    (summary["effort"] <= effort_threshold)
]

targets.to_csv("results/tables/high_richness_low_effort.csv")

print("Potential under-sampled biodiversity hotspots:")
print(targets)