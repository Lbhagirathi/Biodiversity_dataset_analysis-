# Cloning the repository

```bash
git clone https://github.com/Lbhagirathi/Biodiversity_dataset_analysis-
cd Biodiversity_dataset_analysis-/
```
# Installing required packages
### 1. Create virtual environment
```bash
python -m venv venv
```

### 2. Activate environment
```bash
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r packages.txt
```
---

# Data Loading and Pre-Processing
The [DOFbasen database](https://www.gbif.org/occurrence/search?dataset_key=95db4db8-f762-11e1-a439-00145eb45e9a) used has observation records of bird species observed in Denmark from as early as 1750 to present. It contains about 60GB of information with over 40M records till date.
The entire database was taken from GBIF and uploaded to huggingface.co, a simple API call from which helps others go through the database and read its contents, removing the unnecessary trouble of downloading the data.

For the sake of our analysis, we've created a python script which streams the data from huggingface.co and writes the valid entires into a parquet file after necessary filtering.

## Filtering
We've only kept the following necessary columns:
```
"species", "genus", "family", "order", "class", "taxonRank",
"decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
"eventDate", "year", "month", "day", "individualCount",
"occurrenceStatus", "hasCoordinate", "hasGeospatialIssues",
"issue", "stateProvince", "countryCode"
```

During the streaming process itself, we've filtered out entries according to the conditions on the columns:
```
if "class" is not "Aves"
if "hasCoordinate" is not "true"
if "hasGeospatialIssues" is not "false"
if "occurrenceStatus" is not "PRESENT"
if "taxonRank" is not "SPECIES"
if "species" is empty
```
---

# Planned Workflow

## Geographic Scope and Analysis Regions
- We'll use `geopandas` for these operations
- Load Denmark national + regional/municipal boundary shapefiles from GADM
- **Strategy A (Grid):** Overlay regular 0.1° grid on Denmark's bounding box; assign each record to a grid cell by rounding coordinates
- **Strategy B (Administrative):** Assign each record to a Danish region/municipality via spatial join: `geopandas.sjoin`
- Output: two parallel spatial datasets (grid-assigned and admin-assigned) carried into all downstream analyses

## Data Cleaning
- **Taxonomic:** flag and remove records with `TAXON_MATCH_FUZZY` in `issue` column
- **Spatial:** remove records with `coordinateUncertaintyInMeters` > `threshold`; we decide the threshold according to the choice of grid
- **Duplicates:** detect duplicate rows on (`species`, `eventDate`, `decimalLatitude`, `decimalLongitude`); keep one per group — `pandas.DataFrame.duplicated`
- **Missing metadata:** handle contextually per analysis (e.g., drop missing `year` only for temporal analyses, not spatial ones)