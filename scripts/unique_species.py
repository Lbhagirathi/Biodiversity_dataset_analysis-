import pandas as pd

def load_data(filepath):
    print("Loading species column only...")

    df = pd.read_parquet(filepath, columns=["species"])

    unique_species = df["species"].dropna().unique()

    print("Unique species:", len(unique_species))

    # Convert to DataFrame and save
    species_df = pd.DataFrame({"species": unique_species})
    species_df.to_csv("results/unique_species.csv", index=False)

    print("✅ Saved to results/unique_species.csv")

    return species_df


if __name__ == "__main__":
    filepath = "data/dofbasen_birds_filtered.parquet"
    load_data(filepath)