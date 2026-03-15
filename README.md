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

# Loading the data
The [DOFbasen database](https://www.gbif.org/occurrence/search?dataset_key=95db4db8-f762-11e1-a439-00145eb45e9a) used has observation records of bird species observed in Denmark from as early as 1750 to present. It contains about 60GB of information with over 40M records till date.
The entire database was taken from GBIF and uploaded to huggingface.co, a simple API call from which helps others go through the database and read its contents, removing the unnecessary trouble of downloading the data.

For the sake of our analysis, we've created a python script which streams the data from huggingface.co and writes the valid entires into a parquet file after necessary filtering.