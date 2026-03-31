import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

# =========================
# 1. LOAD DATA
# =========================
def load_data(filepath):
    print("Loading required columns...")

    df = pd.read_parquet(
        filepath,
        columns=[
            "species",
            "grid_cell_id",
            "lat_bin",
            "lon_bin"
        ]
    )

    print("Data loaded!")
    print("Total rows:", len(df))
    print("Unique species:", df["species"].nunique())

    return df


# =========================
# 2. SPECIES RICHNESS
# =========================
def compute_richness(df):
    return df.groupby("grid_cell_id")["species"].nunique()


# =========================
# 3. RANGE RESTRICTION
# =========================
def compute_range_restriction(df):

    occupancy = df.groupby("species")["grid_cell_id"].nunique()
    occupancy = occupancy.rename("range_size")

    threshold = occupancy.quantile(0.10)
    restricted = occupancy[occupancy <= threshold]

    return occupancy, restricted


# =========================
# 4. COMBINE METRICS
# =========================
def combine_metrics(df, richness):

    summary = pd.DataFrame({
        "richness": richness
    }).reset_index()

    coords = df.groupby("grid_cell_id")[["lat_bin", "lon_bin"]].first().reset_index()

    summary = pd.merge(summary, coords, on="grid_cell_id")

    return summary


# =========================
# 5. HOTSPOTS
# =========================
def identify_hotspots(summary):

    print("\n🔥 Identifying biodiversity hotspots...")

    threshold = summary["richness"].quantile(0.85)

    hotspots = summary[summary["richness"] >= threshold]

    print("Hotspot threshold:", threshold)
    print("Number of hotspot grid cells:", len(hotspots))

    hotspots.to_csv("results/tables/biodiversity_hotspots.csv", index=False)

    return hotspots


# =========================
# 6. MAPS
# =========================
def plot_maps(summary, hotspots):

    print("📍 Generating biodiversity map...")

    gdf = gpd.GeoDataFrame(
        summary,
        geometry=gpd.points_from_xy(summary["lon_bin"], summary["lat_bin"]),
        crs="EPSG:4326"
    )

    denmark = gpd.read_file("data/gadm41_DNK_0.shp")
    denmark = denmark.to_crs("EPSG:4326")

    print("Total grid cells:", len(gdf))

    fig, ax = plt.subplots(figsize=(10,10))

    # =========================
    # OCEAN BACKGROUND
    # =========================
    ax.set_facecolor("#b7dff5")   # light blue ocean

    # =========================
    # DENMARK LAND
    # =========================
    denmark.plot(
        ax=ax,
        color="#f0f0f0",
        edgecolor="black",
        linewidth=0.8,
        zorder=1
    )

    # =========================
    # ALL GRID CELLS (LAND + SEA)
    # =========================
    gdf.plot(
        ax=ax,
        column="richness",
        cmap="viridis",
        markersize=100,
        legend=True,
        legend_kwds={
            "label": "Species Richness",
            "shrink": 0.6
        },
        alpha=0.9,
        edgecolor="black",
        linewidth=0.2,
        zorder=2
    )

    # =========================
    # HOTSPOTS
    # =========================
    hotspot_gdf = gdf[
        gdf["grid_cell_id"].isin(hotspots["grid_cell_id"])
    ]

    if len(hotspot_gdf) > 0:
        hotspot_gdf.plot(
            ax=ax,
            color="red",
            markersize=200,
            edgecolor="black",
            linewidth=0.5,
            label="Hotspots",
            zorder=3
        )

    # =========================
    # MAP SETTINGS
    # =========================
    ax.set_xlim(7,13)
    ax.set_ylim(54,58)

    ax.set_title(
        "Biodiversity Hotspots in Denmark",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_axis_off()

    ax.legend(loc="lower left")

    plt.savefig(
        "results/plots/biodiversity_hotspots.png",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    print("✅ Map saved!")


# =========================
# 7. STATS + IUCN
# =========================
def compute_stats(df, summary, occupancy, restricted):

    print("\n===== DATASET STATS =====")

    max_rich = summary.loc[summary["richness"].idxmax()]
    min_rich = summary.loc[summary["richness"].idxmin()]

    print("\nHighest richness:\n", max_rich)
    print("\nLowest richness:\n", min_rich)

    abundance = df["species"].value_counts()

    print("\nTop species:\n", abundance.head())
    print("\nRare species:\n", abundance.tail())

    print("\n🌍 Loading IUCN data...")

    iucn = pd.read_excel("data/iucn_status.xlsx")
    iucn.columns = iucn.columns.str.strip()

    iucn = iucn.rename(columns={
        "2025 Scientific name": "species",
        "2025 IUCN Red List category": "status"
    })

    restricted_df = restricted.reset_index()
    restricted_df.columns = ["species","range_size"]

    merged = pd.merge(
        restricted_df,
        iucn[["species","status"]],
        on="species",
        how="left"
    )

    merged = merged.dropna(subset=["status"])

    endangered = merged[
        merged["status"].isin(["CR","EN","VU"])
    ]

    print("\n🚨 Endangered restricted species:\n", endangered)
    print("Total:", len(endangered))

    merged.to_csv(
        "results/tables/restricted_species_with_status.csv",
        index=False
    )

    endangered.to_csv(
        "results/tables/endangered_restricted_species.csv",
        index=False
    )


# =========================
# MAIN
# =========================
def main():

    filepath = "data/grid_assigned.parquet"

    df = load_data(filepath)

    richness = compute_richness(df)

    occupancy, restricted = compute_range_restriction(df)

    summary = combine_metrics(df, richness)

    hotspots = identify_hotspots(summary)

    plot_maps(summary, hotspots)

    compute_stats(df, summary, occupancy, restricted)

    print("\n✅ FULL PIPELINE COMPLETE!")


if __name__ == "__main__":
    main()