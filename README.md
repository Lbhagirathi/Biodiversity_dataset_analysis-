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

# Intoduction
This project analyzes long-term bird biodiversity patterns using the Global Biodiversity Information Facility (GBIF) dataset derived from the DOFbasen Bird Observation Database, which contains citizen-science observations of birds recorded across Denmark from 1750 to the present. The dataset includes more than 40 million occurrence records and is approximately 60 GB in size. To efficiently access and process this large dataset, records are streamed from Hugging Face rather than downloaded locally.

During preprocessing, only biologically relevant and spatially valid records are retained, focusing exclusively on species belonging to the class Aves with verified coordinates and confirmed presence. Essential taxonomic, spatial, and temporal fields are preserved while filtering out incomplete or problematic records.

The analysis focuses on understanding spatial biodiversity patterns by assigning observations to geographic units using two complementary approaches: a regular spatial grid and administrative boundaries of Denmark. Using these spatial groupings, biodiversity indicators such as species richness, range restriction, and observation effort are calculated.

Finally, the processed data are summarized and visualized through an interactive dashboard built with Plotly Dash, enabling exploration of spatial and temporal trends in bird biodiversity. The dashboard allows users to interactively examine species richness, observation effort, and temporal changes across Danish regions.



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

## Biodiversity Indicators
- **Species richness:** `groupby` region → `nunique` on `species` column; compute for both grid and admin aggregations
- **Range restriction:** per species, count number of distinct regions recorded in (`groupby species → nunique region`); flag bottom 10% occupancy as range-restricted
- **Observation effort:** two parallel effort proxies:
    - count total records per region
    - number of unique observation events: unique combinations of (`eventDate` and `decimalLatitude`, `decimalLongitude`) per region

## Interactive Dashboard 
- Framework: **Dash by Plotly**
- Load pre-computed summary Parquet files (not raw records) on app startup
- Components:
  - Choropleth map of Denmark (species richness / effort toggle)
  - Time-series chart (records or species per year)
  - Taxonomic group dropdown
  - Year-range slider
- Mechanisms to link components: selecting a region should update the time-series; selecting a taxonomic group should update the map, etc.
