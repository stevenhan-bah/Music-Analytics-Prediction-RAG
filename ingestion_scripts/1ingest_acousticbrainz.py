import pandas as pd
import os

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = "processed"
MERGED_PARQUET_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_merged.parquet")
MERGED_CSV_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_merged.csv")

#COMPOSITE_KEY = ['mbid', 'submission_offset']

# ── Load: use cached file if it exists, otherwise build it ───────────────────
if os.path.exists(MERGED_PARQUET_PATH):
    print(f"Cached parquet found — loading from {MERGED_PARQUET_PATH}...")
    df = pd.read_parquet(MERGED_PARQUET_PATH)
    print(f"Loaded: {len(df):,} rows")

elif os.path.exists(MERGED_CSV_PATH):
    print(f"Cached CSV found — loading from {MERGED_CSV_PATH}...")
    df = pd.read_csv(MERGED_CSV_PATH)
    print(f"Loaded: {len(df):,} rows")

else:
    print("No cached file found — running one-time merge (this will take a while)...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("  Loading CSVs...")
    rhythm_df   = pd.read_csv("data/acousticbrainz-rhythm.csv")
    lowlevel_df = pd.read_csv("data/acousticbrainz-lowlevel.csv")
    tonal_df    = pd.read_csv("data/acousticbrainz-tonal.csv")


    print("Keeping only one unique MBID by taking median or mode across all submission_offset")
    print("rhythm_df before length: ", len(rhythm_df))
    rhythm_cols = list(rhythm_df.columns[2:])
    print(rhythm_cols)
    rhythm_df = rhythm_df.groupby('mbid')[rhythm_cols].median().reset_index()
    print("rhythm_df after length: ", len(rhythm_df))


    print("lowlevel_df before length: ", len(lowlevel_df))
    lowlevel_cols = list(lowlevel_df.columns[2:])
    print(lowlevel_cols)
    lowlevel_df = lowlevel_df.groupby('mbid')[lowlevel_cols].median().reset_index()
    print("lowlevel_df after length: ", len(lowlevel_df))


    print("tonal_df before length: ", len(tonal_df))
    # 1. Compute the fast mode mapping for your categorical columns
    tonal_key_mode = tonal_df.groupby('mbid')['key_key'].value_counts().groupby(level=0).idxmax().str[1]
    tonal_scale_mode = tonal_df.groupby('mbid')['key_scale'].value_counts().groupby(level=0).idxmax().str[1]

    # 2. Compute the quick numeric medians
    numeric_agg = tonal_df.groupby('mbid').agg({
        'tuning_frequency': 'median',
        'tuning_equal_tempered_deviation': 'median'
    })

    # 3. Combine the results instantly
    tonal_df = numeric_agg.assign(key_key=tonal_key_mode, key_scale=tonal_scale_mode).reset_index()
    print("tonal_df after length: ", len(tonal_df))

    print("  Keeping only MBIDs present in all three files...")
    common_mbids = (
        set(rhythm_df["mbid"])
        & set(lowlevel_df["mbid"])
        & set(tonal_df["mbid"])
    )

    rhythm_df = rhythm_df[rhythm_df["mbid"].isin(common_mbids)]
    lowlevel_df = lowlevel_df[lowlevel_df["mbid"].isin(common_mbids)]
    tonal_df = tonal_df[tonal_df["mbid"].isin(common_mbids)]

    # print("  Removing duplicates on composite key")
    # rhythm_dupes = int(rhythm_df.duplicated(subset = COMPOSITE_KEY).sum())
    # lowlevel_dupes = int(lowlevel_df.duplicated(subset = COMPOSITE_KEY).sum())
    # tonal_dupes = int(tonal_df.duplicated(subset = COMPOSITE_KEY).sum())
    # print(f"    Duplicate rows -> rhythm: {rhythm_dupes:,}, lowlevel: {lowlevel_dupes:,}, tonal: {tonal_dupes:,}")

    # rhythm_df = rhythm_df.drop_duplicates(subset=COMPOSITE_KEY, keep="first")
    # lowlevel_df = lowlevel_df.drop_duplicates(subset=COMPOSITE_KEY, keep="first")
    # tonal_df = tonal_df.drop_duplicates(subset=COMPOSITE_KEY, keep="first")

    print("  Merging...")
    df = rhythm_df.merge(lowlevel_df, on="mbid", how="inner").merge(tonal_df, on="mbid", how="inner")
    
    
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns}")
    print(df.dtypes)
    print(df.info())

    try:
        print(f"  Saving to {MERGED_PARQUET_PATH}...")
        df.to_parquet(MERGED_PARQUET_PATH, compression="snappy", index=False)
    except ImportError:
        print("  Parquet engine not found (pyarrow/fastparquet). Falling back to CSV cache...")
        print(f"  Saving to {MERGED_CSV_PATH}...")
        df.to_csv(MERGED_CSV_PATH, index=False)

    # Free up memory — CSVs no longer needed
    del rhythm_df, lowlevel_df, tonal_df

    print(f"Done — {len(df):,} rows saved. Future runs will skip this step.")

print(df[["mbid", "bpm", "danceability", "average_loudness"]].head())