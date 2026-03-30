import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import os

# =========================
# 1. LOAD DATA
# =========================
def load_data(filepath):

    print("Loading minimal columns...")

    df = pd.read_parquet(
        filepath,
        columns=["species", "decimalLatitude", "decimalLongitude"]
    )

    df = df.dropna(subset=["decimalLatitude", "decimalLongitude"])

    print("Total rows:", len(df))
    print("Unique species:", df["species"].nunique())

    return df


# =========================
# 2. LOAD DENMARK MAP
# =========================
def load_denmark():

    print("Loading Denmark shapefile...")

    denmark = gpd.read_file("data/gadm41_DNK_0.shp")

    # 🔥 CRITICAL FIX: ensure same CRS as lat/lon
    denmark = denmark.to_crs("EPSG:4326")

    print("Denmark CRS:", denmark.crs)

    return denmark


# =========================
# 3. SPECIES DISTRIBUTION
# =========================
def plot_species_distributions(df, denmark):

    print("\n📍 Generating species distribution maps...")

    output_dir = "results/species_maps_raw_2"
    os.makedirs(output_dir, exist_ok=True)

    species_list = df["species"].unique()

    print("Total species:", len(species_list))

    for i, sp in enumerate(species_list):

        sp_df = df[df["species"] == sp]

        if len(sp_df) == 0:
            continue

        # Optional: downsample very large datasets
        if len(sp_df) > 50000:
            sp_df = sp_df.sample(50000, random_state=42)

        # =========================
        # PLOT
        # =========================
        fig, ax = plt.subplots(figsize=(6, 6))

        # ✅ Denmark outline
        denmark.plot(
            ax=ax,
            color="lightgrey",
            edgecolor="black",
            linewidth=0.8,
            zorder=1
        )

        # ✅ Species points
        ax.scatter(
            sp_df["decimalLongitude"],
            sp_df["decimalLatitude"],
            s=1.5,          # 🔥 small markers
            alpha=0.4,
            zorder=2
        )

        # Zoom to Denmark
        ax.set_xlim(7, 13)
        ax.set_ylim(54, 58)

        ax.set_title(sp, fontsize=10)
        ax.set_axis_off()
        ax.set_aspect('auto')

        # =========================
        # SAVE
        # =========================
        filename = sp.replace(" ", "_").replace("/", "_")
        plt.savefig(f"{output_dir}/{filename}.png", dpi=200)
        plt.close()

        # Progress log
        if i % 20 == 0:
            print(f"Processed {i}/{len(species_list)} species")

    print("\n✅ All species maps saved!")


# =========================
# MAIN
# =========================
def main():

    filepath = "data/grid_assigned.parquet"

    df = load_data(filepath)

    denmark = load_denmark()

    plot_species_distributions(df, denmark)


if __name__ == "__main__":
    main()