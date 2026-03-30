import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# 1. LOAD DATA (SAFE SAMPLE)
# =========================
def load_data(filepath):
    df = pd.read_parquet(
        filepath,
        columns=[
            "species",
            "decimalLatitude",
            "decimalLongitude",
            "year",
            "eventDate",
            "individualCount",
            "recordedBy"
        ]
    )

    # SAMPLE for safety (remove later if using Dask)
    # df = df.sample(500000)

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
def create_grid(df, resolution=0.3):
    df["lat_bin"] = np.floor(df["decimalLatitude"] / resolution) * resolution
    df["lon_bin"] = np.floor(df["decimalLongitude"] / resolution) * resolution
    return df


# =========================
# 4. SPECIES RICHNESS
# =========================
def compute_richness(df):
    return df.groupby(["lat_bin", "lon_bin"])["species"].nunique()


# =========================
# 5. OBSERVATION EFFORT
# =========================
def compute_effort(df):
    records = df.groupby(["lat_bin", "lon_bin"]).size()

    df["event_id"] = (
    df["recordedBy"].astype(str) + "_" +
    df["year"].astype(str) + "_" +
    df["eventDate"].astype(str)
)
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
# 7. TEMPORAL RICHNESS
# =========================
def compute_temporal_richness(df):
    return df.groupby(["year", "lat_bin", "lon_bin"])["species"].nunique().reset_index()


# =========================
# 8. COMBINE METRICS
# =========================
def combine_metrics(richness, records, events):
    summary = pd.DataFrame({
        "richness": richness,
        "records": records,
        "events": events
    }).reset_index()

    # ✅ Effort correction
    summary["corrected_richness"] = summary["richness"] / np.log1p(summary["events"])

    return summary


# =========================
# 9. PLOTTING
# =========================
def plot_maps(summary):

    # RAW RICHNESS
    plt.figure()
    plt.scatter(summary["lon_bin"], summary["lat_bin"],
                c=summary["richness"], s=5)
    plt.colorbar(label="Raw Richness")
    plt.title("Raw Species Richness")
    plt.savefig("results/plots/raw_richness.png", dpi=300)

    # CORRECTED RICHNESS
    plt.figure()
    plt.scatter(summary["lon_bin"], summary["lat_bin"],
                c=summary["corrected_richness"], s=5)
    plt.colorbar(label="Corrected Richness")
    plt.title("Effort-Corrected Richness")
    plt.savefig("results/plots/corrected_richness.png", dpi=300)

    # COMPARISON (side-by-side idea simplified)
    plt.figure()
    plt.scatter(summary["richness"], summary["corrected_richness"], s=5)
    plt.xlabel("Raw Richness")
    plt.ylabel("Corrected Richness")
    plt.title("Raw vs Corrected Comparison")
    plt.savefig("results/plots/richness_comparison.png", dpi=300)

    plt.show()


# =========================
# 10. TEMPORAL PLOT
# =========================
def plot_temporal(temporal_df):

    yearly = temporal_df.groupby("year")["species"].mean()

    plt.figure()
    yearly.plot()
    plt.xlabel("Year")
    plt.ylabel("Mean Richness")
    plt.title("Temporal Change in Richness")
    plt.savefig("results/plots/temporal_richness.png", dpi=300)
    plt.show()


# =========================
# 11. SAVE OUTPUTS
# =========================
def save_outputs(summary, occupancy, restricted, temporal):

    summary.to_csv("results/tables/grid_summary.csv", index=False)
    occupancy.to_csv("results/tables/species_occupancy.csv")
    restricted.to_csv("results/tables/range_restricted_species.csv")
    temporal.to_csv("results/tables/temporal_richness.csv", index=False)


# =========================
# MAIN
# =========================
def main():
    filepath = "data/dofbasen_birds_filtered.parquet"

    print("Loading data...")
    df = load_data(filepath)

    print("Cleaning...")
    df = clean_data(df)

    print("Grid mapping...")
    df = create_grid(df)

    print("Richness...")
    richness = compute_richness(df)

    print("Effort...")
    records, events = compute_effort(df)

    print("Range restriction...")
    occupancy, restricted = compute_range_restriction(df)

    print("Temporal richness...")
    temporal = compute_temporal_richness(df)

    print("Combining...")
    summary = combine_metrics(richness, records, events)

    print("Plotting...")
    plot_maps(summary)
    plot_temporal(temporal)

    print("Saving...")
    save_outputs(summary, occupancy, restricted, temporal)

    print("✅ DONE!")


if __name__ == "__main__":
    main()