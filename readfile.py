import requests

url = "https://huggingface.co/datasets/itsmeG/Birds_denmark/resolve/main/Database/occurrence.txt"

columns_needed = [
    "species",
    "genus",
    "decimalLatitude",
    "decimalLongitude",
    "eventDate"
]

# Stream through each line withour downloading locally
with requests.get(url, stream=True) as r:
    # iter_lines makes sure only one line is read at a time,
    # decode_unicode=True converts bytes from server to python string
    rows = r.iter_lines(decode_unicode=True)
    header = next(rows).split("\t")    # gets the first line of dataset that is coloumn name
    
    indices = []        # used to store index of required columns
    for col in columns_needed:
        if col in header:
            idx = header.index(col)
            indices.append(idx)
    print("\t".join(columns_needed)) # adds tab space between each column

    for line in rows:
        row = line.split("\t")
        
        # Filtering rows with blanks
        try:
            filtered = []

            for i in indices:
                filtered.append(row[i])
            print("\t".join(filtered))
        except IndexError: 
            continue


