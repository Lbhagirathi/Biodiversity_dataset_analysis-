import requests
import pandas as pd

url = "https://huggingface.co/datasets/itsmeG/Birds_denmark/resolve/main/Database/occurrence.txt"

columns = [
    "species",
    "genus",
    "decimalLatitude",
    "decimalLongitude",
    "eventDate"
]

with requests.get(url, stream=True) as data:
    file = pd.read_csv(data.raw,usecols=columns,sep="\t",chunksize=5000)
    for chunk in file:
        #print(chunk)    #prints unfiltered data
        filtered = chunk.dropna()
        print(filtered)

