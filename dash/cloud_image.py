import cloudinary
import cloudinary.api
import pandas as pd

cloudinary.config(
    cloud_name="(-_-)",
    api_key="(-_-)",
    api_secret="(-_-)"
)
all_resources = []
next_cursor = None
while True:
    response = cloudinary.api.resources(
        type="upload",
        max_results=100,
        next_cursor=next_cursor
    )

    all_resources.extend(response["resources"])

    next_cursor = response.get("next_cursor")
    if not next_cursor:
        break

data = []
for item in all_resources:
    # publicid had some extra characters so had to filter them to get just species name
    public_id = item["public_id"]
    species = " ".join(public_id.split("_")[:2])
    data.append({
        "species": species,
        "url": item["secure_url"]
    })

df = pd.DataFrame(data)
df.to_csv("cloudinary_images.csv", index=False)

print("Saved cloudinary_images.csv")
