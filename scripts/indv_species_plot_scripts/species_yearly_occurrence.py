import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import os

# =========================
# LOAD DATA
# =========================
def load_data():

    print("Loading data...")

    df = pd.read_parquet(
        "data/grid_assigned.parquet",
        columns=[
            "species",
            "decimalLatitude",
            "decimalLongitude",
            "eventDate"
        ]
    )

    df = df.dropna(subset=["decimalLatitude", "decimalLongitude", "eventDate"])

    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")
    df["year"] = df["eventDate"].dt.year

    # Filter years
    df = df[(df["year"] >= 2000) & (df["year"] <= 2025)]

    print("Rows:", len(df))
    print("Species:", df["species"].nunique())

    return df


# =========================
# LOAD DENMARK MAP
# =========================
def load_denmark():

    print("Loading Denmark shapefile...")

    denmark = gpd.read_file("data/gadm41_DNK_0.shp")
    denmark = denmark.to_crs("EPSG:4326")

    return denmark


# =========================
# PLOT YEARLY MAPS
# =========================
def plot_species_yearly_maps(df, denmark):

    print("\n📍 Generating yearly species maps...")

    base_output = "results/species_yearly_maps"
    os.makedirs(base_output, exist_ok=True)

    species_list = df["species"].unique()

    for i, sp in enumerate(species_list):

        print(f"Processing {i+1}/{len(species_list)}: {sp}")

        sp_df = df[df["species"] == sp]

        # Create species folder
        sp_folder = os.path.join(
            base_output,
            sp.replace(" ", "_").replace("/", "_")
        )
        os.makedirs(sp_folder, exist_ok=True)

        # Loop through years
        for year in range(2000, 2026):

            year_df = sp_df[sp_df["year"] == year]

            if len(year_df) == 0:
                continue

            # Optional downsampling for speed
            if len(year_df) > 50000:
                year_df = year_df.sample(50000, random_state=42)

            # =========================
            # PLOT
            # =========================
            fig, ax = plt.subplots(figsize=(6,6))

            # Ocean background
            ax.set_facecolor("#d6ecff")

            # Denmark land
            denmark.plot(
                ax=ax,
                color="#f2f2f2",
                edgecolor="black",
                linewidth=0.8,
                zorder=1
            )

            # Species points (light blue, transparent)
            ax.scatter(
                year_df["decimalLongitude"],
                year_df["decimalLatitude"],
                s=1.2,
                color="#4da6ff",
                alpha=0.35,
                zorder=2
            )

            # Zoom to Denmark
            ax.set_xlim(7, 13)
            ax.set_ylim(54, 58)

            ax.set_title(f"{sp} ({year})", fontsize=9)
            ax.set_axis_off()

            # =========================
            # SAVE
            # =========================
            filename = f"{year}.png"
            plt.savefig(
                os.path.join(sp_folder, filename),
                dpi=200,
                bbox_inches="tight"
            )

            plt.close()  # 🔥 CRITICAL

        # Progress update
        if i % 10 == 0:
            print(f"Completed {i}/{len(species_list)} species")

    print("\n✅ ALL YEARLY MAPS GENERATED!")


# =========================
# MAIN
# =========================
def main():

    df = load_data()

    denmark = load_denmark()

    plot_species_yearly_maps(df, denmark)


if __name__ == "__main__":
    main()