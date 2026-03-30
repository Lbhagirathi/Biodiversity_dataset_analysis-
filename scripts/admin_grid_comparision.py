import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# =========================
# LOAD DATA
# =========================
def load_data(filepath):

    print("Loading admin-level data...")

    df = pd.read_parquet(
        filepath,
        columns=[
            "species",
            "grid_cell_id",
            "year",
            "eventDate",
            "recordedBy",
            "admin_region"   # 🔥 IMPORTANT COLUMN
        ]
    )

    print("Total rows:", len(df))
    print("Unique species:", df["species"].nunique())
    print("Admin regions:", df["admin_region"].unique())

    return df


# =========================
# ADD EVENT ID
# =========================
def add_effort(df):

    df = df.copy()
    df["event_id"] = (
    df["recordedBy"].astype(str) + "_" +
    df["year"].astype(str) + "_" +
    df["eventDate"].astype(str)
    )

    return df


# =========================
# GRID-LEVEL METRICS
# =========================
def compute_grid_metrics(df):

    print("Computing grid-level metrics...")

    richness = df.groupby("grid_cell_id")["species"].nunique()
    effort = df.groupby("grid_cell_id")["event_id"].nunique()

    grid = pd.DataFrame({
        "richness": richness,
        "effort": effort
    }).reset_index()

    grid["corrected_richness"] = grid["richness"] / np.log1p(grid["effort"])

    return grid


# =========================
# ADMIN-LEVEL METRICS
# =========================
def compute_admin_metrics(df, grid):

    print("\n📊 Computing admin-region biodiversity metrics...")

    # Attach admin info to grid
    admin_map = df.groupby("grid_cell_id")["admin_region"].first().reset_index()
    grid = pd.merge(grid, admin_map, on="grid_cell_id")

    # Aggregate per admin region
    admin_summary = grid.groupby("admin_region").agg({
        "richness": "mean",
        "corrected_richness": "mean",
        "effort": "sum",
        "grid_cell_id": "count"
    }).rename(columns={
        "richness": "mean_grid_richness",
        "corrected_richness": "mean_corrected_richness",
        "grid_cell_id": "num_grids"
    }).reset_index()

    # Total species per region
    total_species = df.groupby("admin_region")["species"].nunique().reset_index()
    total_species = total_species.rename(columns={"species": "total_species"})

    admin_summary = pd.merge(admin_summary, total_species, on="admin_region")

    print(admin_summary)

    return admin_summary


# =========================
# PLOTS
# =========================
def plot_admin_comparison(admin_summary):

    os.makedirs("results/admin_analysis", exist_ok=True)

    # -------------------------
    # 1. TOTAL SPECIES
    # -------------------------
    plt.figure(figsize=(8, 5))
    plt.bar(admin_summary["admin_region"], admin_summary["total_species"])
    plt.xticks(rotation=45)
    plt.title("Total Species per Admin Region")
    plt.ylabel("Species Richness")
    plt.tight_layout()
    plt.savefig("results/admin_analysis/species_per_region.png", dpi=300)
    plt.close()

    # -------------------------
    # 2. CORRECTED RICHNESS
    # -------------------------
    plt.figure(figsize=(8, 5))
    plt.bar(admin_summary["admin_region"], admin_summary["mean_corrected_richness"])
    plt.xticks(rotation=45)
    plt.title("Effort-Corrected Richness per Region")
    plt.ylabel("Corrected Richness")
    plt.tight_layout()
    plt.savefig("results/admin_analysis/corrected_richness_per_region.png", dpi=300)
    plt.close()

    # -------------------------
    # 3. EFFORT vs RICHNESS
    # -------------------------
    plt.figure(figsize=(6, 6))
    plt.scatter(
        admin_summary["effort"],
        admin_summary["total_species"]
    )

    for i, row in admin_summary.iterrows():
        plt.text(row["effort"], row["total_species"], row["admin_region"])

    plt.xlabel("Observation Effort")
    plt.ylabel("Total Species")
    plt.title("Effort vs Richness (Admin Regions)")
    plt.savefig("results/admin_analysis/effort_vs_richness.png", dpi=300)
    plt.close()

    print("📊 Admin comparison plots saved!")


# =========================
# SAVE OUTPUT
# =========================
def save_outputs(admin_summary):

    admin_summary.to_csv("results/admin_analysis/admin_biodiversity_summary.csv", index=False)


# =========================
# MAIN
# =========================
def main():

    filepath = "data/admin_assigned.parquet"

    df = load_data(filepath)

    df = add_effort(df)

    grid = compute_grid_metrics(df)

    admin_summary = compute_admin_metrics(df, grid)

    plot_admin_comparison(admin_summary)

    save_outputs(admin_summary)

    print("\n✅ ADMIN ANALYSIS COMPLETE!")


if __name__ == "__main__":
    main()