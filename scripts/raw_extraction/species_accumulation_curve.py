import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


# =========================
# LOAD DATA
# =========================
def load_data(filepath):

    print("Loading species column...")

    df = pd.read_parquet(
        filepath,
        columns=["species"]
    )

    print("Total records:", len(df))
    print("Unique species:", df["species"].nunique())

    return df


# =========================
# SPECIES ACCUMULATION
# =========================
def species_accumulation(df):

    print("\nComputing species accumulation curve...")

    # Randomize order
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    step = 50000   # sampling interval

    effort = []
    richness = []

    species_seen = set()

    for i in range(0, len(df), step):

        chunk = df.iloc[i:i+step]

        species_seen.update(chunk["species"])

        effort.append(i + step)
        richness.append(len(species_seen))

        if i % (step * 20) == 0:
            print(f"Processed {i:,} records")

    return effort, richness


# =========================
# PLOT CURVE
# =========================
def plot_curve(effort, richness):

    os.makedirs("results/biodiversity_analysis", exist_ok=True)

    plt.figure(figsize=(8,6))

    plt.plot(effort, richness)

    plt.xlabel("Sampling Effort (Number of Records)")
    plt.ylabel("Cumulative Species Detected")

    plt.title("Species Accumulation Curve (Denmark Birds)")

    plt.grid(True)

    plt.savefig(
        "results/biodiversity_analysis/species_accumulation_curve.png",
        dpi=300
    )

    plt.show()

    print("📈 Species accumulation curve saved!")


# =========================
# MAIN
# =========================
def main():

    filepath = "data/dofbasen_birds_filtered.parquet"

    df = load_data(filepath)

    effort, richness = species_accumulation(df)

    plot_curve(effort, richness)

    print("\n✅ Species accumulation analysis complete!")


if __name__ == "__main__":
    main()