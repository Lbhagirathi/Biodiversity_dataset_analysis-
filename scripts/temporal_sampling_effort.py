import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

df = pd.read_parquet(
    "data/grid_assigned.parquet",
    columns=["eventDate","recordedBy"]
)

df["eventDate"] = pd.to_datetime(df["eventDate"])
df["year"] = df["eventDate"].dt.year

df["event_id"] = df["recordedBy"].astype(str) + df["eventDate"].astype(str)

yearly_effort = df.groupby("year")["event_id"].nunique()

plt.figure(figsize=(7,4))

yearly_effort.plot()

plt.xlabel("Year")
plt.ylabel("Observation Events")
plt.title("Sampling Effort Through Time")

plt.savefig("results/plots/temporal_sampling_effort.png", dpi=300)
plt.close()