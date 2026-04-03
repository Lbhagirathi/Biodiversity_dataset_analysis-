import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# =========================
# PATHS
# =========================

GRID_GPKG = "denmark_grid.gpkg"
HOTSPOT_CSV = "results/tables/biodiversity_hotspots.csv"
PARK_CSV = "results/tables/park_biodiversity_summary.csv"

OUTPUT_FIG = "results/plots/hotspots_vs_parks_map.png"


# =========================
# LOAD DATA
# =========================

print("Loading grid polygons...")
grid = gpd.read_file(GRID_GPKG).to_crs("EPSG:4326")

print("Loading hotspot table...")
hotspots = pd.read_csv(HOTSPOT_CSV)

print("Loading park summary...")
parks_summary = pd.read_csv(PARK_CSV)

print("Grid cells:", len(grid))
print("Hotspot cells:", len(hotspots))
print("Parks:", len(parks_summary))


# =========================
# ATTACH HOTSPOT INFO
# =========================

grid["is_hotspot"] = grid["grid_cell_id"].isin(hotspots["grid_cell_id"])


# =========================
# CREATE PARK POLYGONS
# =========================

parks_data = {
    "park_name":[
        "Thy",
        "Mols_Bjerge",
        "Wadden_Sea",
        "Skjoldungernes_Land",
        "Kongernes_Nordsjaelland"
    ],
    "lat":[56.95,56.23,55.35,55.62,55.98],
    "lon":[8.40,10.52,8.45,11.88,12.30]
}

parks = pd.DataFrame(parks_data)

parks["geometry"] = parks.apply(
    lambda r: Point(r["lon"], r["lat"]).buffer(0.3),
    axis=1
)

parks = gpd.GeoDataFrame(parks, geometry="geometry", crs="EPSG:4326")


# =========================
# PLOT MAP
# =========================

print("Generating comparison map...")

fig, ax = plt.subplots(figsize=(10,12))

# Ocean background
ax.set_facecolor("#b7dff5")

# All grid cells
grid.plot(
    ax=ax,
    color="#eeeeee",
    edgecolor="white",
    linewidth=0.1
)

# Hotspot grid cells
grid[grid["is_hotspot"]].plot(
    ax=ax,
    color="red",
    edgecolor="darkred",
    linewidth=0.5,
    label="Biodiversity Hotspots"
)

# Park polygons
parks.boundary.plot(
    ax=ax,
    color="darkgreen",
    linewidth=2,
    label="National Parks"
)

# Park fill
parks.plot(
    ax=ax,
    color="lightgreen",
    alpha=0.4
)

ax.set_title(
    "Biodiversity Hotspots vs National Parks in Denmark",
    fontsize=15,
    fontweight="bold"
)

ax.set_xlim(8.0,15.3)
ax.set_ylim(54.5,57.8)

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

plt.legend()

plt.tight_layout()

plt.savefig(OUTPUT_FIG, dpi=600)

plt.show()

print("Saved:", OUTPUT_FIG)