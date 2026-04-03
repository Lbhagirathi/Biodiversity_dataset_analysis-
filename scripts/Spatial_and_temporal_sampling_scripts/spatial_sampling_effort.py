import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os

# =====================================================
# FILE PATHS
# =====================================================

DATA_PATH = "data/grid_assigned.parquet"
GRID_PATH = "denmark_grid.gpkg"
ADMIN_PATH = "denmark_admin.gpkg"

OUTPUT_PLOT = "results/plots/sampling_effort_map.png"

os.makedirs("results/plots", exist_ok=True)


# =====================================================
# LOAD OCCURRENCE DATA
# =====================================================

def load_data():

    print("Loading observation data...")

    df = pd.read_parquet(
        DATA_PATH,
        columns=[
            "grid_cell_id",
            "eventDate",
            "recordedBy"
        ]
    )

    print("Total records:", len(df))

    return df


# =====================================================
# COMPUTE SAMPLING EFFORT
# =====================================================

def compute_sampling_effort(df):

    print("Computing sampling effort...")

    # Create unique observation event
    df["event_id"] = df["recordedBy"].astype(str) + "_" + df["eventDate"].astype(str)

    effort = df.groupby("grid_cell_id")["event_id"].nunique()

    effort = effort.reset_index()
    effort.columns = ["grid_cell_id","sampling_effort"]

    print("Grid cells with effort:", len(effort))

    return effort


# =====================================================
# LOAD SPATIAL LAYERS
# =====================================================

def load_spatial_layers():

    print("Loading spatial layers...")

    grid = gpd.read_file(GRID_PATH)
    denmark = gpd.read_file(ADMIN_PATH).dissolve()

    grid = grid.to_crs("EPSG:4326")
    denmark = denmark.to_crs("EPSG:4326")

    return grid, denmark


# =====================================================
# MERGE EFFORT WITH GRID
# =====================================================

def attach_effort(grid, effort):

    grid_effort = grid.merge(
        effort,
        on="grid_cell_id",
        how="left"
    )

    grid_effort["sampling_effort"] = grid_effort["sampling_effort"].fillna(0)

    print("Cells with observations:",
          (grid_effort["sampling_effort"] > 0).sum())

    return grid_effort


# =====================================================
# PLOT SAMPLING EFFORT MAP
# =====================================================

def plot_effort(grid_effort, denmark):

    print("Generating sampling effort map...")

    fig, ax = plt.subplots(figsize=(10,12))

    # Ocean background
    ax.set_facecolor("#b7dff5")

    # Grid cells
    grid_effort.plot(
        ax=ax,
        column="sampling_effort",
        cmap="plasma",
        edgecolor="white",
        linewidth=0.1,
        legend=True,
        legend_kwds={
            "label":"Sampling Effort (Unique Observation Events)",
            "shrink":0.6
        }
    )

    # Denmark boundary
    denmark.plot(
        ax=ax,
        color="none",
        edgecolor="black",
        linewidth=1.2
    )

    ax.set_title(
        "Sampling Effort Across Denmark (Bird Observations)",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.set_xlim(8.0,15.3)
    ax.set_ylim(54.5,57.8)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_PLOT,
        dpi=600,
        bbox_inches="tight"
    )

    plt.close()

    print("Map saved to:", OUTPUT_PLOT)


# =====================================================
# MAIN PIPELINE
# =====================================================

def main():

    df = load_data()

    effort = compute_sampling_effort(df)

    grid, denmark = load_spatial_layers()

    grid_effort = attach_effort(grid, effort)

    plot_effort(grid_effort, denmark)

    print("\nSampling effort analysis complete")


if __name__ == "__main__":
    main()