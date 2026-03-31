import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import os

# =========================
# FILE PATHS
# =========================

HOTSPOT_FILE = "results/tables/biodiversity_hotspots.csv"
SHAPEFILE = "data/gadm41_DNK_0.shp"

os.makedirs("results/plots", exist_ok=True)
os.makedirs("results/tables", exist_ok=True)

# =========================
# LOAD HOTSPOTS
# =========================

hotspots = pd.read_csv(HOTSPOT_FILE)

gdf_hotspots = gpd.GeoDataFrame(
    hotspots,
    geometry=gpd.points_from_xy(hotspots["lon_bin"], hotspots["lat_bin"]),
    crs="EPSG:4326"
)

print("Total hotspot grids:", len(gdf_hotspots))

# =========================
# PARK COORDINATES
# =========================

parks = pd.DataFrame({
    "park":[
        "Thy",
        "Mols_Bjerge",
        "Wadden_Sea",
        "Skjoldungernes_Land",
        "Kongernes_Nordsjaelland"
    ],
    "lat":[56.95,56.23,55.35,55.62,55.98],
    "lon":[8.40,10.52,8.45,11.88,12.30]
})

gdf_parks = gpd.GeoDataFrame(
    parks,
    geometry=gpd.points_from_xy(parks["lon"], parks["lat"]),
    crs="EPSG:4326"
)

# =========================
# LOAD DENMARK MAP
# =========================

denmark = gpd.read_file(SHAPEFILE).to_crs("EPSG:4326")

# =========================
# DETERMINE HOTSPOTS INSIDE PARKS
# =========================

radius = 0.5  # degrees (~50 km)

inside = []
outside = []

for idx, hotspot in gdf_hotspots.iterrows():

    dist = np.sqrt(
        (parks["lat"] - hotspot["lat_bin"])**2 +
        (parks["lon"] - hotspot["lon_bin"])**2
    )

    if np.min(dist) <= radius:
        inside.append(idx)
    else:
        outside.append(idx)

hotspots["inside_park"] = False
hotspots.loc[inside, "inside_park"] = True

# =========================
# SAVE ANALYSIS TABLE
# =========================

hotspots.to_csv(
    "results/tables/hotspot_protection_analysis.csv",
    index=False
)

# =========================
# CALCULATE PROPORTIONS
# =========================

inside_count = hotspots["inside_park"].sum()
total = len(hotspots)

percent_inside = 100 * inside_count / total
percent_outside = 100 - percent_inside

print("\nHotspots inside parks:", inside_count)
print("Hotspots outside parks:", total - inside_count)

print("\n% inside protected areas:", round(percent_inside,2))
print("% outside protected areas:", round(percent_outside,2))

# =========================
# MAP VISUALIZATION
# =========================

fig, ax = plt.subplots(figsize=(10,10))

# ocean background
ax.set_facecolor("#b7dff5")

# denmark
denmark.plot(
    ax=ax,
    color="#f0f0f0",
    edgecolor="black",
    linewidth=0.8
)

# hotspots outside parks
gdf_hotspots[~hotspots["inside_park"]].plot(
    ax=ax,
    color="orange",
    markersize=120,
    label="Hotspots outside parks",
    edgecolor="black"
)

# hotspots inside parks
gdf_hotspots[hotspots["inside_park"]].plot(
    ax=ax,
    color="red",
    markersize=150,
    label="Hotspots inside parks",
    edgecolor="black"
)

# parks
gdf_parks.plot(
    ax=ax,
    color="blue",
    markersize=200,
    marker="*",
    label="National Parks"
)

ax.set_xlim(7,13)
ax.set_ylim(54,58)

ax.set_title(
    "Biodiversity Hotspots vs Protected Areas in Denmark",
    fontsize=16,
    fontweight="bold"
)

ax.set_axis_off()

ax.legend()

plt.savefig(
    "results/plots/hotspots_vs_parks.png",
    dpi=600,
    bbox_inches="tight"
)

plt.show()

print("\nMap saved: results/plots/hotspots_vs_parks.png")