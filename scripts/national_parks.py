import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import os

# =========================
# SETTINGS
# =========================
DATA_PATH = "data/grid_assigned.parquet"
SHAPEFILE = "data/gadm41_DNK_0.shp"

OUTPUT_TABLE = "results/tables/park_biodiversity_summary.csv"
OUTPUT_MAP_FOLDER = "results/plots/parks"

os.makedirs("results/tables", exist_ok=True)
os.makedirs(OUTPUT_MAP_FOLDER, exist_ok=True)


# =========================
# 1. LOAD DATA
# =========================
def load_data():

    print("Loading dataset...")

    df = pd.read_parquet(
        DATA_PATH,
        columns=[
            "species",
            "grid_cell_id",
            "lat_bin",
            "lon_bin",
            "decimalLatitude",
            "decimalLongitude"
        ]
    )

    df = df.dropna(subset=["decimalLatitude", "decimalLongitude"])

    print("Total rows:", len(df))
    print("Unique species:", df["species"].nunique())

    return df


# =========================
# 2. NATIONAL PARK COORDINATES
# =========================
def get_parks():

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

    return parks


# =========================
# 3. FIND GRID CELLS AROUND PARKS
# =========================
def assign_park_grids(df, parks, radius=0.5):

    print("Mapping parks to grid cells...")

    grid_df = df[["grid_cell_id","lat_bin","lon_bin"]].drop_duplicates()

    park_grid_map = {}

    for _, row in parks.iterrows():

        dist = np.sqrt(
            (grid_df["lat_bin"] - row["lat"])**2 +
            (grid_df["lon_bin"] - row["lon"])**2
        )

        grids = grid_df[dist <= radius]["grid_cell_id"].values

        park_grid_map[row["park"]] = grids

        print(row["park"], "->", len(grids), "grid cells")

    return park_grid_map


# =========================
# 4. EXTRACT PARK DATA
# =========================
def extract_park_data(df, park_grid_map):

    print("Extracting observations inside parks...")

    park_data = []

    for park, grids in park_grid_map.items():

        sub = df[df["grid_cell_id"].isin(grids)].copy()

        sub["park"] = park

        park_data.append(sub)

    park_df = pd.concat(park_data)

    print("Total park observations:", len(park_df))

    return park_df


# =========================
# 5. BIODIVERSITY METRICS
# =========================
def compute_metrics(park_df):

    print("Computing biodiversity metrics...")

    richness = park_df.groupby("park")["species"].nunique()

    abundance = park_df.groupby("park")["species"].count()

    summary = pd.DataFrame({
        "species_richness": richness,
        "abundance": abundance
    }).reset_index()

    print(summary)

    summary.to_csv(OUTPUT_TABLE, index=False)

    print("Saved:", OUTPUT_TABLE)

    return summary


# =========================
# 6. PLOT RAW DISTRIBUTION
# =========================
def plot_park_maps(park_df):

    print("Generating park occurrence maps...")

    denmark = gpd.read_file(SHAPEFILE).to_crs("EPSG:4326")

    for park in park_df["park"].unique():

        sub = park_df[park_df["park"] == park]

        if len(sub) == 0:
            continue

        fig, ax = plt.subplots(figsize=(6,6))

        # Ocean background
        ax.set_facecolor("#b7dff5")

        # Denmark land
        denmark.plot(
            ax=ax,
            color="#f0f0f0",
            edgecolor="black",
            linewidth=0.8
        )

        # Occurrence points
        ax.scatter(
            sub["decimalLongitude"],
            sub["decimalLatitude"],
            s=2,
            alpha=0.4,
            color="dodgerblue"
        )

        ax.set_xlim(7,13)
        ax.set_ylim(54,58)

        ax.set_title(f"{park} - Bird Occurrences")

        ax.set_axis_off()

        filename = f"{OUTPUT_MAP_FOLDER}/{park}.png"

        plt.savefig(filename, dpi=300)
        plt.close()

        print("Saved:", filename)


# =========================
# MAIN
# =========================
def main():

    df = load_data()

    parks = get_parks()

    park_grid_map = assign_park_grids(df, parks)

    park_df = extract_park_data(df, park_grid_map)

    compute_metrics(park_df)

    plot_park_maps(park_df)

    print("\n✅ NATIONAL PARK BIODIVERSITY ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()