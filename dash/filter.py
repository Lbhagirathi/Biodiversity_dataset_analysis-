"""
So what this code do is filter all the data and find if the species is endangered eexotic common extinct or migrating and makes a parquet and csv file for it which would act as a filter for the dashboard
"""
import pandas as pd
import wikipedia
import time

# Fetch info from Wikipedia
def fetch_status(species):
    try:
        summary = wikipedia.summary(species, sentences=15, auto_suggest=True).lower()

        if "extinct" in summary:
            return "Extinct"

        elif any(word in summary for word in [
            "endangered", "threatened", "vulnerable", "near threatened"
        ]):
            return "Endangered"

        elif any(word in summary for word in [
            "introduced", "exotic", "invasive"
        ]):
            return "Exotic"

        elif any(word in summary for word in [
            "migratory", "migration", "migrates"
        ]):
            return "Migrating"

        else:
            return "Common"

    except wikipedia.exceptions.DisambiguationError:
        return "Unknown"

    except wikipedia.exceptions.PageError:
        return "Unknown"

    except Exception as e:
        print(f"Error for {species}: {e}")
        return "Unknown"

def build_species_status(input_file, output_file="species_status.parquet"):
    if input_file.endswith(".csv"):
        df = pd.read_csv(input_file, usecols=["species"])

    elif input_file.endswith(".parquet"):
        df = pd.read_parquet(input_file, columns=["species"])

    else:
        raise ValueError("Unsupported file format")

    species_list = df["species"].dropna().unique()
    total = len(species_list)

    print(f"Found {total} unique species.\n")

    results = []

    for i, sp in enumerate(species_list):
        print(f"[{i+1}/{total}] {sp}")

        status = fetch_status(sp)

        results.append({
            "species": sp,
            "status": status
        })

        time.sleep(0.1)  # avoid being blocked cause we may get blocked thinking we are robot

    result_df = pd.DataFrame(results)

    # Save both formats
    result_df.to_parquet(output_file, index=False)
    result_df.to_csv("species_status.csv", index=False)

    print(f"Saved: {output_file} + species_status.csv")

if __name__ == "__main__":
    build_species_status("birds.csv")
