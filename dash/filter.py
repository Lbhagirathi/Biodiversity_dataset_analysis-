"""
So what this code do is filter all the data and find if the species is endangered eexotic common extinct or migrating and makes a parquet and csv file for it which would act as a filter for the dashboard
"""
import pandas as pd
import wikipedia
import time

# Fetch info from Wikipedia
def fetch_status(species):
    try:
        page = wikipedia.page(species, auto_suggest=True)
        title = page.title
        summary = page.summary.lower()
        if title.lower() != species.lower():
            common_name = title
        else:
            common_name = "Unknown"

            if "commonly known as" in summary:
                try:
                    common_name = summary.split("commonly known as")[1].split(",")[0].strip()
                except:
                    pass

        if "extinct" in summary:
            return "Extinct" , common_name

        elif any(word in summary for word in [
            "endangered", "threatened", "vulnerable", "near threatened"
        ]):
            return "Endangered", common_name

        elif any(word in summary for word in [
            "introduced", "exotic", "invasive"
        ]):
            return "Exotic", common_name

        elif any(word in summary for word in [
            "migratory", "migration", "migrates"
        ]):
            return "Migrating", common_name

        else:
            return "Common", common_name

    except wikipedia.exceptions.DisambiguationError:
        return "Unknown","Unknown"

    except wikipedia.exceptions.PageError:
        return "Unknown","Unknown"

    except Exception as e:
        print(f"Error for {species}: {e}")
        return "Unknown","Unknown"

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

        status,common_name = fetch_status(sp)

        results.append({
            "species": sp,
            "common_name": common_name,
            "status": status
        })

        time.sleep(0.1)  # avoid being blocked cause we may get blocked thinking we are robot

    result_df = pd.DataFrame(results)

    # Save both formats
    result_df.to_parquet(output_file, index=False)
    result_df.to_csv("unique_species_all.csv", index=False)

    print(f"Saved: {output_file} + species_status.csv")

if __name__ == "__main__":
    build_species_status("unique_species.csv")
