import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.patches import Patch
import os

# =====================================================
# FILE PATHS
# =====================================================

HOTSPOT_FILE = "results/tables/biodiversity_hotspots.csv"
GRID_FILE = "denmark_grid.gpkg"
DENMARK_SHAPE = "data/gadm41_DNK_0.shp"

OUTPUT_TABLE = "results/tables/hotspot_protection_analysis.csv"
OUTPUT_MAP = "results/plots/hotspots_vs_parks_final.png"

os.makedirs("results/tables", exist_ok=True)
os.makedirs("results/plots", exist_ok=True)

# =====================================================
# LOAD HOTSPOTS
# =====================================================

print("Loading hotspot grid cells...")

hotspots = pd.read_csv(HOTSPOT_FILE)

gdf_hotspots = gpd.GeoDataFrame(
    hotspots,
    geometry=gpd.points_from_xy(
        hotspots["lon_bin"],
        hotspots["lat_bin"]
    ),
    crs="EPSG:4326"
)

print("Total hotspot cells:", len(gdf_hotspots))


# =====================================================
# LOAD GRID POLYGONS
# =====================================================

print("Loading Denmark grid...")

grid = gpd.read_file(GRID_FILE).to_crs("EPSG:4326")

# attach richness to grid
grid_hotspots = grid.merge(
    hotspots,
    on="grid_cell_id",
    how="inner"
)

print("Hotspot grid polygons:", len(grid_hotspots))


# =====================================================
# CREATE NATIONAL PARK POLYGONS
# =====================================================

print("Creating park polygons...")

parks_data = {
    "park_name":[
        "Thy",
        "Mols Bjerge",
        "Wadden Sea",
        "Skjoldungernes Land",
        "Kongernes Nordsjaelland"
    ],
    "lat":[56.95,56.23,55.35,55.62,55.98],
    "lon":[8.40,10.52,8.45,11.88,12.30]
}

parks_df = pd.DataFrame(parks_data)

parks_df["geometry"] = parks_df.apply(
    lambda r: Point(r["lon"], r["lat"]).buffer(0.3),
    axis=1
)

parks = gpd.GeoDataFrame(parks_df, geometry="geometry", crs="EPSG:4326")

print("Parks created:", len(parks))


# =====================================================
# LOAD DENMARK OUTLINE
# =====================================================

denmark = gpd.read_file(DENMARK_SHAPE).to_crs("EPSG:4326")


# =====================================================
# SPATIAL JOIN: HOTSPOTS INSIDE PARKS
# =====================================================

print("Running spatial join...")

hotspot_parks = gpd.sjoin(
    grid_hotspots,
    parks,
    how="left",
    predicate="intersects"
)

hotspot_parks["inside_park"] = hotspot_parks["park_name"].notna()

inside_count = hotspot_parks["inside_park"].sum()
total = len(hotspot_parks)

print("\nHotspots inside parks:", inside_count)
print("Hotspots outside parks:", total - inside_count)


# =====================================================
# SAVE ANALYSIS TABLE
# =====================================================

hotspot_parks[[
    "grid_cell_id",
    "richness",
    "park_name",
    "inside_park"
]].to_csv(OUTPUT_TABLE, index=False)

print("Saved table:", OUTPUT_TABLE)


# =====================================================
# MAP VISUALIZATION
# =====================================================

print("Generating final map...")

fig, ax = plt.subplots(figsize=(10,10))

# ocean background
ax.set_facecolor("#b7dff5")

# Denmark land
denmark.plot(
    ax=ax,
    color="#f0f0f0",
    edgecolor="black",
    linewidth=0.8
)

# hotspot grids outside parks
hotspot_parks[~hotspot_parks["inside_park"]].plot(
    ax=ax,
    color="#f39c12",
    edgecolor="darkorange",
    linewidth=0.6
)

# hotspot grids inside parks
hotspot_parks[hotspot_parks["inside_park"]].plot(
    ax=ax,
    color="#e74c3c",
    edgecolor="darkred",
    linewidth=0.6
)

# park polygons
parks.plot(
    ax=ax,
    color="lightgreen",
    edgecolor="darkgreen",
    linewidth=2,
    alpha=0.6
)

# =====================================================
# LEGEND (manual for geopandas)
# =====================================================

legend_elements = [

    Patch(
        facecolor="#e74c3c",
        edgecolor="darkred",
        label="Hotspots inside parks"
    ),

    Patch(
        facecolor="#f39c12",
        edgecolor="darkorange",
        label="Hotspots outside parks"
    ),

    Patch(
        facecolor="lightgreen",
        edgecolor="darkgreen",
        label="National parks"
    )
]

ax.legend(handles=legend_elements, loc="lower left")


# =====================================================
# MAP SETTINGS
# =====================================================

ax.set_xlim(7,13)
ax.set_ylim(54,58)

ax.set_title(
    "Bird Biodiversity Hotspots vs National Parks in Denmark",
    fontsize=16,
    fontweight="bold"
)

ax.set_axis_off()

plt.savefig(
    OUTPUT_MAP,
    dpi=600,
    bbox_inches="tight"
)

plt.show()

print("Map saved:", OUTPUT_MAP)

print("\n✅ HOTSPOT–PROTECTED AREA ANALYSIS COMPLETE")