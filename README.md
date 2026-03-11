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

# How it Works
A simple API call from hugginface.co helps others go through the database and  read its contents, this removes the unneccesary trouble of downloading the data (hoping cloud works fine). This database used has the count of species of birds from Denmark observed over various lattitude over different years. The entire database was taken from GBIF and uploaded to huggingface.co, the database contains about 60GB worth of information.

