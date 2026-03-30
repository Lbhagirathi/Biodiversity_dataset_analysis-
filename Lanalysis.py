# import pandas as pd

# df = pd.read_parquet(
#     "grid_assignedfiltered.parquet",
#     columns=[
#         "species",
#         "decimalLatitude",
#         "decimalLongitude",
#         "eventDate",
#         "month",
#         "year",
#         "individualCount"
#     ]
# )

# print(df.head())

import pyarrow.parquet as pq

pq_file = pq.ParquetFile("data/grid_assigned.parquet")
print(pq_file.schema)