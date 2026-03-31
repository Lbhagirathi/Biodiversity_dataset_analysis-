import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

df = pd.read_parquet(
    "data/grid_assigned.parquet",
    columns=["grid_cell_id","lat_bin","lon_bin","eventDate","recordedBy"]
)

# Create event ID
df["event_id"] = df["recordedBy"].astype(str) + "_" + df["eventDate"].astype(str)

effort = df.groupby("grid_cell_id")["event_id"].nunique()

coords = df.groupby("grid_cell_id")[["lat_bin","lon_bin"]].first()

summary = pd.concat([effort, coords], axis=1).reset_index()
summary.columns = ["grid_cell_id","effort","lat_bin","lon_bin"]

gdf = gpd.GeoDataFrame(
    summary,
    geometry=gpd.points_from_xy(summary["lon_bin"], summary["lat_bin"]),
    crs="EPSG:4326"
)

denmark = gpd.read_file("data/gadm41_DNK_0.shp").to_crs("EPSG:4326")

fig, ax = plt.subplots(figsize=(8,8))

denmark.plot(ax=ax, color="lightgrey", edgecolor="black")

gdf.plot(
    ax=ax,
    column="effort",
    cmap="plasma",
    markersize=80,
    legend=True
)

ax.set_title("Sampling Effort Across Denmark")
ax.set_axis_off()

plt.savefig("results/plots/sampling_effort_map.png", dpi=300)
plt.close()