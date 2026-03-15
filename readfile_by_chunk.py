import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# =============================================================================
# CONFIGURATION
# =============================================================================
URL = "https://huggingface.co/datasets/itsmeG/Birds_denmark/resolve/main/Database/occurrence.txt"

COLUMNS_NEEDED = [
    "species", "genus", "family", "order", "class", "taxonRank",
    "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
    "eventDate", "year", "month", "day", "individualCount",
    "occurrenceStatus", "hasCoordinate", "hasGeospatialIssues",
    "issue", "stateProvince", "countryCode"
]

OUTPUT_PATH = "dofbasen_birds_filtered.parquet"

# Every BATCH_SIZE rows that pass filters, we flush to disk and clear the buffer.
# 100,000 rows is efficient, small enough that the buffer never grows beyond ~50-100 MB at most.
BATCH_SIZE = 100_000


# =============================================================================
# TYPE CONVERSION HELPERS
# =============================================================================
# We define the data types for each column explicitly upfront.
# PyArrow needs to know the schema before it can write the first batch, so we can't rely on inference.
# All values arrive as strings from the stream, so we also define how to convert them.

def convert_record(record):
    """
    Converts a raw dictionary of strings (as read from the TSV stream) into properly typed Python values.
    
    pd.to_numeric / int / float conversion is NOT done here because we are working at the single-row level and that would be slow.
    Instead we convert types at the batch level using pandas, which is vectorised and fast.
    """
    return record  # Pass through — type conversion happens at batch level below


def cast_batch_types(batch_df):
    """
    Takes a small pandas DataFrame (one batch) and casts columns to their correct types.
    Using errors='coerce' means any value that cannot be converted (empty string, 'NA', a stray word) becomes NaN instead of crashing the script.
    """
    float_cols = ["decimalLatitude", "decimalLongitude",
                  "coordinateUncertaintyInMeters"]
    int_cols   = ["year", "month", "day", "individualCount"]

    for col in float_cols:
        if col in batch_df.columns:
            batch_df[col] = pd.to_numeric(batch_df[col], errors="coerce")

    for col in int_cols:
        if col in batch_df.columns:
            # Int64 is pandas' nullable integer — it can hold NaN.
            # Regular int64 cannot, and would crash on missing values.
            batch_df[col] = pd.to_numeric(
                batch_df[col], errors="coerce"
            ).astype("Int64")

    if "eventDate" in batch_df.columns:
        batch_df["eventDate"] = pd.to_datetime(
            batch_df["eventDate"], errors="coerce"
        )

    return batch_df


# =============================================================================
# MAIN STREAMING FUNCTION
# =============================================================================
def stream_and_filter(url, columns_needed, output_path, batch_size):
    """
    Streams the occurrence file line by line, filters rows in-place, and writes valid records to a Parquet file in fixed-size batches.

    Memory footprint at any point = one batch buffer (at most batch_size rows).
    The rest has either been written to disk or was never loaded at all.
    """

    buffer = [] # Temporary holding area — gets cleared every batch_size rows
    parquet_writer = None

    skipped_malformed = 0
    skipped_filtered  = 0
    total_kept        = 0
    total_processed   = 0

    print("Opening streaming connection...")

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        rows = r.iter_lines(decode_unicode=True)

        # Consume the header line before the main loop
        header = next(rows).split("\t")
        print(f"File header has {len(header)} columns total.")

        # Map each desired column name to its position index in the header
        col_to_idx = {
            col: header.index(col)
            for col in columns_needed
            if col in header
        }

        missing_cols = [c for c in columns_needed if c not in header]
        if missing_cols:
            print(f"WARNING: Columns not found in file (will be absent): {missing_cols}")

        print(f"Streaming with batch size = {batch_size:,} rows\n")

        for line in rows:
            total_processed += 1

            # Progress report — important to confirm RAM is staying stable
            if total_processed % 1_000_000 == 0:
                print(f"  → {total_processed:,} processed | "
                      f"{total_kept:,} kept | "
                      f"Buffer: {len(buffer):,} | "
                      f"Filtered: {skipped_filtered:,} | "
                      f"Malformed: {skipped_malformed:,}")

            row = line.split("\t")

            # Extract fields:
            try:
                record = {col: row[idx] for col, idx in col_to_idx.items()}
            except IndexError:
                skipped_malformed += 1
                continue

            # Quality filters (same as before):
            # All comparisons use strings because the values from the TSV are raw strings.
            # This accounts for errors caused by stuff like 'true' != True in Python
            if record.get("class", "")!= "Aves": skipped_filtered += 1; continue
            if record.get("hasCoordinate", "")!= "true": skipped_filtered += 1; continue
            if record.get("hasGeospatialIssues","")!= "false": skipped_filtered += 1; continue
            if record.get("occurrenceStatus", "")!= "PRESENT": skipped_filtered += 1; continue
            if record.get("taxonRank", "")!= "SPECIES": skipped_filtered += 1; continue
            if not record.get("species", "").strip(): skipped_filtered += 1; continue

            # Add to buffer
            buffer.append(record)
            total_kept += 1

            # Flush to disk when buffer is full:
            # Once the buffer reaches batch_size, we convert it to a DataFrame, cast types, write it to the Parquet file, and then CLEAR the buffer.
            # Python's garbage collector then reclaims that memory. RAM stays flat.
            if len(buffer) >= batch_size:
                parquet_writer = _flush_buffer(
                    buffer, parquet_writer, output_path, col_to_idx
                )
                buffer.clear()  # This is what keeps RAM usage from growing indefinitely

        # Flush any remaining rows in the buffer after the loop ends:
        # The last batch will almost certainly be smaller than batch_size, so we need one final flush to make sure no records are lost.
        if buffer:
            parquet_writer = _flush_buffer(
                buffer, parquet_writer, output_path, col_to_idx
            )
            buffer.clear()

    # Close the Parquet writer to finalise the file on disk
    if parquet_writer:
        parquet_writer.close()

    # =========================================================================
    # Summary
    # =========================================================================
    print(f"\n{'='*55}")
    print(f"  Streaming complete.")
    print(f"  Total rows processed : {total_processed:,}")
    print(f"  Valid rows kept      : {total_kept:,}")
    print(f"  Filtered out         : {skipped_filtered:,}")
    print(f"  Malformed (skipped)  : {skipped_malformed:,}")
    print(f"  Output saved to      : '{output_path}'")
    print(f"{'='*55}\n")
    print(f"In future sessions, load with:\n  df = pd.read_parquet('{output_path}')")


def _flush_buffer(buffer, parquet_writer, output_path, col_to_idx):
    """
    Converts the current buffer (a list of dicts) into a typed pandas DataFrame, converts that to a PyArrow Table, and appends it to the Parquet file.
    The ParquetWriter is created on the first flush (when parquet_writer is None) because we need at least one batch to infer the PyArrow schema.
    Every subsequent flush reuses the same writer and appends to the same file.
    
    Returns the (possibly newly created) parquet_writer so the caller can hold a reference to it.
    """
    # Convert buffer to DataFrame and cast types
    batch_df = pd.DataFrame(buffer)
    batch_df = cast_batch_types(batch_df)

    # Convert to a PyArrow Table — this is PyArrow's native in-memory format
    table = pa.Table.from_pandas(batch_df, preserve_index=False)

    if parquet_writer is None:
        # First batch: create the writer, which also creates the output file
        # and writes the schema header. The schema is inferred from this first table.
        parquet_writer = pq.ParquetWriter(output_path, table.schema)
        print(f"  [First batch] Created Parquet file with schema from "
              f"{len(buffer):,} rows.")

    # Append this batch to the file
    parquet_writer.write_table(table)
    return parquet_writer


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    stream_and_filter(URL, COLUMNS_NEEDED, OUTPUT_PATH, BATCH_SIZE)