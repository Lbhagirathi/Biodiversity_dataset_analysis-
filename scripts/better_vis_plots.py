import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# =========================
# FILE PATHS
# =========================
GRID_PARQUET_PATH = "data/grid_assigned.parquet"
GRID_GPKG_PATH    = "denmark_grid.gpkg"
ADMIN_GPKG_PATH   = "denmark_admin.gpkg"


# =========================
# LOAD DATA
# =========================
def load_data():

    print("Loading occurrence data...")

    df = pd.read_parquet(
        GRID_PARQUET_PATH,
        columns=["species","grid_cell_id"]
    )

    print("Records:", len(df))
    print("Unique species:", df["species"].nunique())
    print("Grid cells:", df["grid_cell_id"].nunique())

    return df


# =========================
# LOAD SPATIAL DATA
# =========================
def load_spatial_layers():

    print("Loading grid polygons...")

    grid_gdf = gpd.read_file(GRID_GPKG_PATH)

    print("Grid cells:", len(grid_gdf))

    print("Loading Denmark boundary...")

    denmark = gpd.read_file(ADMIN_GPKG_PATH)

    grid_gdf = grid_gdf.to_crs("EPSG:4326")
    denmark = denmark.to_crs("EPSG:4326")

    return grid_gdf, denmark


# =========================
# SPECIES RICHNESS
# =========================
def compute_richness(df):

    richness = df.groupby("grid_cell_id")["species"].nunique()

    richness = richness.reset_index()
    richness.columns = ["grid_cell_id","species_richness"]

    return richness


# =========================
# HOTSPOTS
# =========================
def identify_hotspots(grid_richness):

    threshold = grid_richness["species_richness"].quantile(0.85)

    hotspots = grid_richness[
        grid_richness["species_richness"] >= threshold
    ]

    print("Hotspot threshold:", threshold)
    print("Hotspot cells:", len(hotspots))

    return hotspots


# =========================
# MERGE WITH GRID
# =========================
def attach_richness(grid_gdf, richness):

    grid_richness = grid_gdf.merge(
        richness,
        on="grid_cell_id",
        how="left"
    )

    grid_richness["species_richness"] = grid_richness["species_richness"].fillna(0)

    print("Cells with records:", (grid_richness["species_richness"] > 0).sum())

    return grid_richness


# =========================
# PLOT MAP
# =========================
from matplotlib.lines import Line2D

# =========================
# PLOT MAP
# =========================
def plot_richness(grid_richness, denmark, hotspots):

    print("Generating biodiversity map...")

    fig, ax = plt.subplots(figsize=(10,12))

    # Ocean background
    ax.set_facecolor("#b7dff5")

    # -------------------------
    # Base richness map
    # -------------------------
    grid_richness.plot(
        ax=ax,
        column="species_richness",
        cmap="YlOrRd",
        edgecolor="white",
        linewidth=0.1,
        legend=True,
        legend_kwds={
            "label":"Species richness (unique species per grid cell)",
            "shrink":0.6
        }
    )

    # -------------------------
    # Denmark boundary
    # -------------------------
    denmark.plot(
        ax=ax,
        color="none",
        edgecolor="black",
        linewidth=1.2,
        zorder=2
    )

    # -------------------------
    # Hotspot overlay (glow)
    # -------------------------
    hotspot_cells = grid_richness[
        grid_richness["grid_cell_id"].isin(hotspots["grid_cell_id"])
    ]

    hotspot_cells.plot(
        ax=ax,
        color="red",
        alpha=0.35,
        edgecolor="black",
        linewidth=1.5,
        zorder=3
    )

    # -------------------------
    # Map formatting
    # -------------------------
    ax.set_title(
        "Bird Species Richness per 0.3° Grid Cell — Denmark",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlim(8.0,15.3)
    ax.set_ylim(54.5,57.8)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # -------------------------
    # Custom legend
    # -------------------------
    legend_elements = [
        Line2D(
            [0], [0],
            marker='s',
            color='w',
            markerfacecolor='red',
            markersize=12,
            alpha=0.5,
            label="Hotspots (top 15% richness)"
        )
    ]

    ax.legend(handles=legend_elements, loc="lower left")

    plt.tight_layout()

    plt.savefig(
        "results/plots/species_richness_grid.png",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    print("Map saved.")


# =========================
# MAIN
# =========================
def main():

    df = load_data()

    grid_gdf, denmark = load_spatial_layers()

    richness = compute_richness(df)

    grid_richness = attach_richness(grid_gdf, richness)

    hotspots = identify_hotspots(grid_richness)

    plot_richness(grid_richness, denmark, hotspots)


if __name__ == "__main__":
    main()