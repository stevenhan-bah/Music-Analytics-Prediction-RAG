import pandas as pd
import numpy as np
import os


OUTPUT_DIR = "processed"
MERGED_PARQUET_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_merged.parquet")
MERGED_CSV_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_merged.csv")
FULL_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_full.parquet")
HIGHLEVEL_CSV_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_before_dedup.csv")



print(f"Loading base data from {MERGED_PARQUET_PATH}...")
df = pd.read_parquet(MERGED_PARQUET_PATH)

print("Loading high level")
highlevel_df = pd.read_csv(HIGHLEVEL_CSV_PATH)


categorical_cols = [item for item in list(highlevel_df.columns) if item not in ['mbid', 'mood_happy_prob','mood_aggressive_prob']]


# 2. Compute the quick numeric medians (done once)
final_df = highlevel_df.groupby('mbid').agg({
    'mood_happy_prob': 'median',
    'mood_aggressive_prob': 'median'
}).reset_index()

# 1. & 3. Loop through categorical columns and assign instantly
for col in categorical_cols:
    mode_mapping = highlevel_df.groupby('mbid')[col].value_counts().groupby(level=0).idxmax().str[1]
    final_df = final_df.assign(**{col: mode_mapping.values})

print(final_df.shape)

df_final = df.merge(final_df, on="mbid", how="inner")

print(f"\nFinal merged dataframe: {len(df_final):,} rows")
print(f"Columns: {list(df_final.columns)}")

# ── 6. Save to Parquet for S3/Athena ─────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)
df_final.to_parquet(FULL_PATH, compression="snappy", index=False)
print(f"\nSaved: {FULL_PATH}")


print(df_final[["mbid", "bpm", "danceability", "mood_happy", "genre"]].head())

