import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


# =========================
# LOAD DATA
# =========================
def load_data():

    print("Loading dataset...")

    df = pd.read_parquet(
        "data/grid_assigned.parquet",
        columns=[
            "species",
            "grid_cell_id",
            "eventDate",
            "recordedBy"
        ]
    )

    print("Rows:", len(df))
    print("Unique species:", df["species"].nunique())

    return df


# =========================
# COMPUTE METRICS
# =========================
def compute_metrics(df):

    print("Computing richness and effort...")

    # Species richness
    richness = df.groupby("grid_cell_id")["species"].nunique()

    # Correct event ID (prevents merging events)
    df["event_id"] = (
        df["recordedBy"].astype(str) + "_" +
        df["eventDate"].astype(str)
    )

    # Observation effort
    effort = df.groupby("grid_cell_id")["event_id"].nunique()

    summary = pd.DataFrame({
        "richness": richness,
        "effort": effort
    })

    # Effort corrected richness (for bias comparison)
    summary["effort_corrected"] = summary["richness"] / np.log1p(summary["effort"])

    print(summary.head())

    return summary


# =========================
# SAMPLING BIAS PLOT
# =========================
def plot_bias(summary):

    print("Generating sampling bias plot...")

    plt.figure(figsize=(7,6))

    x = summary["effort"]
    y = summary["richness"]

    # scatter
    plt.scatter(x, y, s=6, alpha=0.4)

    # log transform effort for regression
    logx = np.log10(x)

    # regression
    coeffs = np.polyfit(logx, y, 1)
    poly = np.poly1d(coeffs)

    # create smooth x values
    xs = np.linspace(logx.min(), logx.max(), 200)
    ys = poly(xs)

    plt.plot(10**xs, ys, linewidth=2)

    plt.xscale("log")

    plt.xlabel("Observation Effort (log scale)")
    plt.ylabel("Species Richness")

    plt.title("Sampling Bias: Effort vs Species Richness")

    plt.tight_layout()

    plt.savefig("results/plots/sampling_bias.png", dpi=300)

    plt.close()

    print("Sampling bias plot saved.")


# =========================
# MAIN
# =========================
def main():

    df = load_data()

    summary = compute_metrics(df)

    plot_bias(summary)

    print("✅ Sampling bias analysis complete!")


if __name__ == "__main__":
    main()