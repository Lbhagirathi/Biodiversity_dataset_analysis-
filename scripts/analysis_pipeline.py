import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# 1. LOAD DATA (MEMORY SAFE)
# =========================
def load_data(filepath):
    df = pd.read_parquet(
        filepath,
        columns=[
            "species",
            "decimalLatitude",
            "decimalLongitude",
            "year",
            "individualCount",
            "recordedBy"
        ]
    )
    df = df.sample(500000)
    return df


# =========================
# 2. CLEAN DATA
# =========================
def clean_data(df):
    df = df.dropna(subset=["species", "decimalLatitude", "decimalLongitude"])
    df = df[df["individualCount"] > 0]
    return df


# =========================
# 3. GRID MAPPING
# =========================
def create_grid(df, resolution=0.1):
    df["lat_bin"] = np.floor(df["decimalLatitude"] / resolution) * resolution
    df["lon_bin"] = np.floor(df["decimalLongitude"] / resolution) * resolution
    return df


# =========================
# 4. SPECIES RICHNESS
# =========================
def compute_richness(df):
    richness = df.groupby(["lat_bin", "lon_bin"])["species"].nunique()
    return richness


# =========================
# 5. OBSERVATION EFFORT
# =========================
def compute_effort(df):
    # total records
    records = df.groupby(["lat_bin", "lon_bin"]).size()

    # unique observation events
    df["event_id"] = df["recordedBy"].astype(str) + "_" + df["year"].astype(str)
    events = df.groupby(["lat_bin", "lon_bin"])["event_id"].nunique()

    return records, events


# =========================
# 6. RANGE RESTRICTION
# =========================
def compute_range_restriction(df):
    occupancy = df.groupby("species")[["lat_bin", "lon_bin"]].nunique()
    occupancy["range_size"] = occupancy["lat_bin"] * occupancy["lon_bin"]

    threshold = occupancy["range_size"].quantile(0.10)
    restricted = occupancy[occupancy["range_size"] <= threshold]

    return occupancy, restricted


# =========================
# 7. COMBINE RESULTS
# =========================
def combine_metrics(richness, records, events):
    summary = pd.DataFrame({
        "richness": richness,
        "records": records,
        "events": events
    }).reset_index()

    return summary


# =========================
# 8. PLOTTING
# =========================
def plot_richness(summary):
    plt.figure()

    plt.scatter(
        summary["lon_bin"],
        summary["lat_bin"],
        c=summary["richness"],
        s=5
    )

    plt.colorbar(label="Species Richness")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Species Richness Map")

    plt.savefig("../results/plots/richness_map.png", dpi=300)
    plt.show()


# =========================
# 9. SAVE OUTPUTS
# =========================
def save_outputs(summary, occupancy, restricted):
    summary.to_csv("../results/tables/grid_summary.csv", index=False)
    occupancy.to_csv("../results/tables/species_occupancy.csv")
    restricted.to_csv("../results/tables/range_restricted_species.csv")


# =========================
# MAIN
# =========================
def main():
    filepath = "../data/dofbasen_birds_filtered.parquet"

    print("Loading data...")
    df = load_data(filepath)

    print("Cleaning data...")
    df = clean_data(df)

    print("Creating grid...")
    df = create_grid(df)

    print("Computing richness...")
    richness = compute_richness(df)

    print("Computing effort...")
    records, events = compute_effort(df)

    print("Computing range restriction...")
    occupancy, restricted = compute_range_restriction(df)

    print("Combining metrics...")
    summary = combine_metrics(richness, records, events)

    print("Plotting...")
    plot_richness(summary)

    print("Saving outputs...")
    save_outputs(summary, occupancy, restricted)

    print("Done!")


if __name__ == "__main__":
    main()