import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import os

# =====================================================
# PATH SETTINGS
# =====================================================

DATA_PATH = "data/grid_assigned.parquet"
GRID_PATH = "denmark_grid.gpkg"

OUTPUT_TABLE = "results/tables/park_biodiversity_summary.csv"
OUTPUT_MAP_DIR = "results/plots/parks"

os.makedirs("results/tables", exist_ok=True)
os.makedirs(OUTPUT_MAP_DIR, exist_ok=True)

# =====================================================
# 1 LOAD DATA
# =====================================================

def load_data():

    print("Loading biodiversity dataset...")

    df = pd.read_parquet(
        DATA_PATH,
        columns=[
            "species",
            "grid_cell_id",
            "decimalLatitude",
            "decimalLongitude"
        ]
    )

    df = df.dropna(subset=["decimalLatitude","decimalLongitude"])

    print("Total observations:", len(df))
    print("Unique species:", df["species"].nunique())

    return df


# =====================================================
# 2 LOAD GRID
# =====================================================

def load_grid():

    print("Loading Denmark grid...")

    grid = gpd.read_file(GRID_PATH)
    grid = grid.to_crs("EPSG:4326")

    print("Grid cells:", len(grid))

    return grid


# =====================================================
# 3 CREATE NATIONAL PARK POLYGONS
# =====================================================

def create_parks():

    print("Creating park polygons from coordinates...")

    parks_data = {
        "park_name":[
            "Thy",
            "Mols_Bjerge",
            "Wadden_Sea",
            "Skjoldungernes_Land",
            "Kongernes_Nordsjaelland"
        ],
        "lat":[56.95,56.23,55.35,55.62,55.98],
        "lon":[8.40,10.52,8.45,11.88,12.30]
    }

    parks = pd.DataFrame(parks_data)

    parks["geometry"] = parks.apply(
        lambda r: Point(r["lon"], r["lat"]).buffer(0.3),
        axis=1
    )

    parks_gdf = gpd.GeoDataFrame(parks, geometry="geometry", crs="EPSG:4326")

    print("Created", len(parks_gdf), "park polygons")

    return parks_gdf


# =====================================================
# 4 CONVERT OCCURRENCES TO GEO
# =====================================================

def convert_to_geodata(df):

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["decimalLongitude"],
            df["decimalLatitude"]
        ),
        crs="EPSG:4326"
    )

    return gdf


# =====================================================
# 5 ASSIGN OBSERVATIONS TO PARKS
# =====================================================

def assign_observations_to_parks(points, parks, grid):

    print("Assigning grid cells to parks...")

    # spatial join grid with parks
    grid_parks = gpd.sjoin(
        grid,
        parks[["park_name","geometry"]],
        how="inner",
        predicate="intersects"
    )

    print("Grid cells intersecting parks:", len(grid_parks))

    # keep only grid id + park name
    grid_parks = grid_parks[["grid_cell_id","park_name"]]

    # merge park name into observations
    park_points = points.merge(
        grid_parks,
        on="grid_cell_id",
        how="inner"
    )

    print("Observations inside parks:", len(park_points))

    return park_points


# =====================================================
# 6 COMPUTE PARK BIODIVERSITY METRICS
# =====================================================

def compute_park_metrics(park_points):

    print("Computing park biodiversity metrics...")

    richness = park_points.groupby("park_name")["species"].nunique()
    abundance = park_points.groupby("park_name")["species"].count()

    summary = pd.DataFrame({
        "species_richness": richness,
        "abundance": abundance
    }).reset_index()

    print(summary)

    summary.to_csv(OUTPUT_TABLE, index=False)

    print("Saved:", OUTPUT_TABLE)

    return summary


# =====================================================
# 7 GRID RICHNESS
# =====================================================

def compute_grid_richness(df):

    richness = df.groupby("grid_cell_id")["species"].nunique()

    richness = richness.reset_index()
    richness.columns = ["grid_cell_id","species_richness"]

    return richness


# =====================================================
# 8 PLOT GRID RICHNESS + PARKS
# =====================================================

def plot_grid_richness(grid, richness, parks):

    print("Plotting biodiversity richness map...")

    grid = grid.merge(
        richness,
        on="grid_cell_id",
        how="left"
    )

    grid["species_richness"] = grid["species_richness"].fillna(0)

    fig, ax = plt.subplots(figsize=(10,12))

    ax.set_facecolor("#b7dff5")

    grid.plot(
        ax=ax,
        column="species_richness",
        cmap="YlOrRd",
        edgecolor="white",
        linewidth=0.1,
        legend=True,
        legend_kwds={
            "label":"Species Richness"
        }
    )

    parks.boundary.plot(
        ax=ax,
        color="black",
        linewidth=2
    )

    ax.set_title("Species Richness per Grid Cell with National Parks")

    ax.set_xlim(8.0,15.3)
    ax.set_ylim(54.5,57.8)

    plt.tight_layout()

    plt.savefig(
        f"{OUTPUT_MAP_DIR}/grid_richness_with_parks.png",
        dpi=600
    )

    plt.close()

    print("Saved grid richness map")


# =====================================================
# 9 RAW OCCURRENCES PER PARK
# =====================================================

def plot_raw_occurrences(park_points, parks):

    print("Generating park occurrence maps...")

    for park in park_points["park_name"].unique():

        sub = park_points[park_points["park_name"] == park]

        park_poly = parks[parks["park_name"] == park]

        fig, ax = plt.subplots(figsize=(6,6))

        ax.set_facecolor("#b7dff5")

        parks.plot(
            ax=ax,
            color="#f0f0f0",
            edgecolor="black"
        )

        park_poly.plot(
            ax=ax,
            color="lightgreen",
            edgecolor="darkgreen"
        )

        ax.scatter(
            sub["decimalLongitude"],
            sub["decimalLatitude"],
            s=2,
            alpha=0.4,
            color="dodgerblue"
        )

        ax.set_title(f"{park} – Bird Occurrences")

        ax.set_axis_off()

        filename = park.replace(" ","_")

        plt.savefig(
            f"{OUTPUT_MAP_DIR}/{filename}_occurrences.png",
            dpi=300
        )

        plt.close()

        print("Saved:", filename)


# =====================================================
# 10 PARK COMPARISON PLOT
# =====================================================

def plot_park_comparison(summary):

    plt.figure(figsize=(8,5))

    plt.bar(
        summary["park_name"],
        summary["species_richness"],
        color="darkgreen"
    )

    plt.xticks(rotation=45)

    plt.ylabel("Species Richness")

    plt.title("Species Richness across Danish National Parks")

    plt.tight_layout()

    plt.savefig(
        f"{OUTPUT_MAP_DIR}/park_richness_comparison.png",
        dpi=300
    )

    plt.close()


# =====================================================
# MAIN PIPELINE
# =====================================================

def main():

    df = load_data()

    grid = load_grid()

    parks = create_parks()

    points = convert_to_geodata(df)

    park_points = assign_observations_to_parks(points, parks,grid)

    summary = compute_park_metrics(park_points)

    richness = compute_grid_richness(df)

    plot_grid_richness(grid, richness, parks)

    plot_raw_occurrences(park_points, parks)

    plot_park_comparison(summary)

    print("\n✅ NATIONAL PARK BIODIVERSITY ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()