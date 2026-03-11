# Cloning the repository

```bash
git clone https://github.com/Lbhagirathi/Biodiversity_dataset_analysis-
```
```bash
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


# Database
The entire database was taken from GBIF and uploaded into huggingface.co, this had to be done so that anyone can access the database from their remote pc without going through the trouble of dowloading the 60GB databse. A simple API call from the website helps others go through the database and  read its contents, this removes the unneccesary trouble of downloading the data (hoping cloud works fine). This database used has the count of species of birds from Denmark observed over various lattitude over different years.
