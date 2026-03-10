import requests

url = "https://huggingface.co/datasets/itsmeG/Birds_denmark/resolve/main/Database/occurrence.txt"

# Stream line by line and does NOT save the full file locally
with requests.get(url, stream=True) as r:
    for line in r.iter_lines():
        print(line.decode())
