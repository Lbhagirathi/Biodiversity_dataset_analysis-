import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
            "year",
            "eventDate",
            "recordedBy",
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
# 3. OBSERVATION EFFORT
# =========================
def compute_effort(df):

    df["event_id"] = (
    df["recordedBy"].astype(str) + "_" +
    df["year"].astype(str) + "_" +
    df["eventDate"].astype(str)
    )

    return df.groupby("grid_cell_id")["event_id"].nunique()


# =========================
# 4. RANGE RESTRICTION
# =========================
def compute_range_restriction(df):

    occupancy = df.groupby("species")["grid_cell_id"].nunique()
    occupancy = occupancy.rename("range_size")

    threshold = occupancy.quantile(0.10)
    restricted = occupancy[occupancy <= threshold]

    return occupancy, restricted


# =========================
# 5. COMBINE METRICS
# =========================
def combine_metrics(df, richness, events):

    summary = pd.DataFrame({
        "richness": richness,
        "events": events
    }).reset_index()

    summary["corrected_richness"] = summary["richness"] / np.log1p(summary["events"])

    # Add spatial coordinates
    coords = df.groupby("grid_cell_id")[["lat_bin", "lon_bin"]].first().reset_index()
    summary = pd.merge(summary, coords, on="grid_cell_id")

    return summary


# =========================
# 6. HOTSPOT DETECTION
# =========================
def identify_hotspots(summary):

    print("\n🔥 Identifying biodiversity hotspots...")

    threshold = summary["corrected_richness"].quantile(0.90)
    hotspots = summary[summary["corrected_richness"] >= threshold]

    print("Hotspot threshold:", threshold)
    print("Number of hotspot grid cells:", len(hotspots))

    hotspots.to_csv("results/tables/biodiversity_hotspots.csv", index=False)

    return hotspots


# =========================
# 7. MAP VISUALIZATION
# =========================
def plot_maps(summary, hotspots):

    import geopandas as gpd

    # Convert points
    gdf = gpd.GeoDataFrame(
        summary,
        geometry=gpd.points_from_xy(summary["lon_bin"], summary["lat_bin"]),
        crs="EPSG:4326"
    )

    # =========================
    # LOAD HIGH-RES DENMARK MAP (GADM)
    # =========================
    denmark = gpd.read_file("data/gadm41_DNK_0.shp")

    # Ensure same CRS
    gdf = gdf.to_crs(denmark.crs)

    # =========================
    # PLOT
    # =========================
    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot boundary ONLY (so colors are visible)
    denmark.plot(
        ax=ax,
        color="none",
        edgecolor="black",
        linewidth=1
    )

    # Plot richness (with color scale)
    gdf.plot(
        ax=ax,
        column="corrected_richness",
        cmap="viridis",
        markersize=8,
        legend=True,
        alpha=0.8
    )

    # Highlight hotspots
    hotspot_gdf = gdf[gdf["grid_cell_id"].isin(hotspots["grid_cell_id"])]
    hotspot_gdf.plot(
        ax=ax,
        color="red",
        markersize=15,
        label="Hotspots"
    )

    plt.title("Biodiversity Hotspots (Denmark)")

    plt.legend()

    plt.savefig("results/plots/hotspots_map.png", dpi=300)
    plt.show()
# =========================
# 8. BASIC VISUALIZATION
# =========================
def plot_results(summary):

    plt.figure()
    plt.scatter(range(len(summary)), summary["richness"], s=5)
    plt.title("Raw Richness")
    plt.savefig("results/plots/raw_richness.png")

    plt.figure()
    plt.scatter(range(len(summary)), summary["corrected_richness"], s=5)
    plt.title("Corrected Richness")
    plt.savefig("results/plots/corrected_richness.png")

    plt.figure()
    plt.scatter(summary["richness"], summary["corrected_richness"], s=5)
    plt.title("Raw vs Corrected")
    plt.savefig("results/plots/comparison.png")

    plt.show()


# =========================
# 9. STATS + IUCN
# =========================
def compute_stats(df, summary, occupancy, restricted):

    print("\n===== DATASET STATS =====")

    # Richness extremes
    max_rich = summary.loc[summary["richness"].idxmax()]
    min_rich = summary.loc[summary["richness"].idxmin()]

    print("\nHighest richness grid:\n", max_rich)
    print("\nLowest richness grid:\n", min_rich)

    # Abundance
    abundance = df["species"].value_counts()

    print("\nTop species:\n", abundance.head())
    print("\nRare species:\n", abundance.tail())

    # -------------------------
    # IUCN
    # -------------------------
    print("\n🌍 Loading IUCN data...")

    iucn = pd.read_excel("data/iucn_status.xlsx")
    iucn.columns = iucn.columns.str.strip()

    iucn = iucn.rename(columns={
        "2025 Scientific name": "species",
        "2025 IUCN Red List category": "status"
    })

    restricted_df = restricted.reset_index()
    restricted_df.columns = ["species", "range_size"]

    merged = pd.merge(restricted_df, iucn[["species", "status"]], on="species", how="left")
    merged = merged.dropna(subset=["status"])

    endangered = merged[merged["status"].isin(["CR", "EN", "VU"])]

    print("\n🚨 Endangered restricted species:\n", endangered)
    print("Total:", len(endangered))

    merged.to_csv("results/tables/restricted_species_with_status.csv", index=False)
    endangered.to_csv("results/tables/endangered_restricted_species.csv", index=False)


# =========================
# MAIN
# =========================
def main():

    filepath = "data/grid_assigned.parquet"

    df = load_data(filepath)

    richness = compute_richness(df)
    events = compute_effort(df)

    occupancy, restricted = compute_range_restriction(df)

    summary = combine_metrics(df, richness, events)

    hotspots = identify_hotspots(summary)

    plot_results(summary)
    plot_maps(summary, hotspots)

    compute_stats(df, summary, occupancy, restricted)

    print("\n✅ FULL PIPELINE COMPLETE!")


if __name__ == "__main__":
    main()