import os
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

# =========================
# CREATE OUTPUT FOLDERS
# =========================
os.makedirs("results/species_maps/grid", exist_ok=True)
os.makedirs("results/species_maps/raw", exist_ok=True)


# =========================
# LOAD DATA
# =========================
def load_data(filepath):

    df = pd.read_parquet(
        filepath,
        columns=[
            "species",
            "grid_cell_id",
            "eventDate",
            "lat_bin",
            "lon_bin",
            "decimalLatitude",
            "decimalLongitude"
        ]
    )

    return df


# =========================
# PLOT FUNCTION
# =========================
def plot_species_maps(df):

    print("🌍 Loading Denmark map...")
    denmark = gpd.read_file("data/gadm41_DNK_0.shp").to_crs("EPSG:4326")

    species_list = df["species"].unique()

    print("Total species:", len(species_list))

    for i, sp in enumerate(species_list):

        print(f"Processing {i+1}/{len(species_list)}: {sp}")

        sp_df = df[df["species"] == sp]

        # =========================
        # 1. GRID-LEVEL MAP
        # =========================
        grid = sp_df.groupby("grid_cell_id")[["lat_bin", "lon_bin"]].first().reset_index()

        gdf_grid = gpd.GeoDataFrame(
            grid,
            geometry=gpd.points_from_xy(grid["lon_bin"], grid["lat_bin"]),
            crs="EPSG:4326"
        )

        fig, ax = plt.subplots(figsize=(6, 6))

        denmark.plot(ax=ax, color="lightgrey", edgecolor="black")

        gdf_grid.plot(
            ax=ax,
            color="blue",
            markersize=40,
            alpha=0.7
        )

        ax.set_title(f"{sp} (Grid Distribution)")
        ax.set_axis_off()

        filename = f"results/species_maps/grid/{sp.replace(' ', '_')}_grid.png"
        plt.savefig(filename, dpi=200, bbox_inches="tight")
        plt.close()   # 🔥 CRITICAL

        # =========================
        # 2. RAW POINT MAP
        # =========================
        raw = sp_df.dropna(subset=["decimalLatitude", "decimalLongitude"])

        if len(raw) > 0:

            gdf_raw = gpd.GeoDataFrame(
                raw,
                geometry=gpd.points_from_xy(raw["decimalLongitude"], raw["decimalLatitude"]),
                crs="EPSG:4326"
            )

            fig, ax = plt.subplots(figsize=(6, 6))

            denmark.plot(ax=ax, color="lightgrey", edgecolor="black")

            gdf_raw.plot(
                ax=ax,
                color="green",
                markersize=5,
                alpha=0.5
            )

            ax.set_title(f"{sp} (Raw Occurrences)")
            ax.set_axis_off()

            filename = f"results/species_maps/raw/{sp.replace(' ', '_')}_raw.png"
            plt.savefig(filename, dpi=200, bbox_inches="tight")
            plt.close()   # 🔥 CRITICAL

    print("✅ All species maps generated!")


# =========================
# MAIN
# =========================
def main():

    filepath = "data/grid_assigned.parquet"

    df = load_data(filepath)

    plot_species_maps(df)


if __name__ == "__main__":
    main()