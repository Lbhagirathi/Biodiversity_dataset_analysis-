import pandas as pd
import matplotlib.pyplot as plt
import os

# =========================
# LOAD DATA
# =========================
def load_data():

    print("Loading data...")

    df = pd.read_parquet(
        "data/grid_assigned.parquet",
        columns=["species", "eventDate"]
    )

    df = df.dropna(subset=["species", "eventDate"])

    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")

    df["year"] = df["eventDate"].dt.year
    df["month"] = df["eventDate"].dt.month

    df = df[(df["year"] >= 2000) & (df["year"] <= 2025)]

    print("Rows:", len(df))
    print("Species:", df["species"].nunique())

    return df


# =========================
# MONTHLY BAR PLOTS
# =========================
def plot_monthly_yearly(df):

    print("\nGenerating monthly bar plots...")

    output_base = "results/species_monthly_yearly"
    os.makedirs(output_base, exist_ok=True)

    species_list = df["species"].unique()

    for i, sp in enumerate(species_list):

        print(f"Processing {i+1}/{len(species_list)}: {sp}")

        sp_df = df[df["species"] == sp]

        # species folder
        sp_folder = os.path.join(
            output_base,
            sp.replace(" ", "_").replace("/", "_")
        )

        os.makedirs(sp_folder, exist_ok=True)

        for year in range(2000, 2026):

            year_df = sp_df[sp_df["year"] == year]

            if len(year_df) == 0:
                continue

            monthly_counts = year_df.groupby("month").size()

            # Ensure all 12 months exist
            monthly_counts = monthly_counts.reindex(range(1,13), fill_value=0)

            # =========================
            # PLOT
            # =========================
            fig, ax = plt.subplots(figsize=(6,4))

            ax.bar(range(1,13), monthly_counts.values)

            ax.set_xticks(range(1,13))
            ax.set_xticklabels(
                ["Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"],
                rotation=45
            )

            ax.set_ylabel("Number of Observations")
            ax.set_xlabel("Month")

            ax.set_title(f"{sp} ({year})")

            plt.tight_layout()

            # =========================
            # SAVE
            # =========================
            filename = f"{year}.png"

            plt.savefig(
                os.path.join(sp_folder, filename),
                dpi=200
            )

            plt.close()   # CRITICAL (prevents RAM crash)

        if i % 10 == 0:
            print(f"Completed {i}/{len(species_list)} species")

    print("\n✅ All monthly plots generated!")


# =========================
# MAIN
# =========================
def main():

    df = load_data()

    plot_monthly_yearly(df)


if __name__ == "__main__":
    main()