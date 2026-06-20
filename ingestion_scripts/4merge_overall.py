import pandas as pd
import os

OUTPUT_DIR   = "processed"
AB_PATH      = os.path.join(OUTPUT_DIR, "acousticbrainz_full.parquet")
MB_PATH      = os.path.join(OUTPUT_DIR, "musicbrainz_canonical.parquet")
MASTER_PATH  = os.path.join(OUTPUT_DIR, "master_dataset.parquet")

if os.path.exists(MASTER_PATH):
    print(f"Master dataset already exists — loading from {MASTER_PATH}...")
    df = pd.read_parquet(MASTER_PATH)

else:
    # ── Load both cached parquets ──────────────────────────────────────────────
    print("Loading AcousticBrainz data...")
    ab_df = pd.read_parquet(AB_PATH)
    print(f"  → {len(ab_df):,} rows")

    print("Loading MusicBrainz Canonical data...")
    mb_df = pd.read_parquet(MB_PATH)
    print(f"  → {len(mb_df):,} rows")

    #recording_redirect_df = pd.read_csv("data/canonical_recording_redirect.csv",
    #usecols=["recording_mbid", "canonical_recording_mbid"])

    # ── Merge on mbid ──────────────────────────────────────────────────────────
    print("Merging...")
    #df = ab_df.merge(mb_df, on="mbid", how="left")

    # Pass 1: direct match
    direct = ab_df.merge(mb_df, on="mbid", how="inner")


    print(f"\nFinal merged dataframe: {len(direct):,} rows")
    print(f"Columns: {list(direct.columns)}")




    # matched = direct[direct["title"].notna()].copy()
    # unmatched = direct[direct["title"].isna()].drop(
    #     columns=mb_df.columns.difference(["mbid"])
    # )

    # print(f"Direct matches:    {len(matched):,}")
    # print(f"Still unmatched:        {len(unmatched):,}")

    # Pass 2: for rows that didn't match, try via recording redirect
    # redirect_match = (
    #     unmatched[["mbid"]]
    #     .merge(recording_redirect_df, left_on="mbid",
    #         right_on="recording_mbid", how="left")
    #     .merge(mb_df.rename(columns={"mbid": "canonical_recording_mbid"}),
    #         on="canonical_recording_mbid", how="left")
    #     .drop(columns=["recording_mbid", "canonical_recording_mbid"])
    # )

    # redirect_matched = unmatched.drop(columns=["title"], errors="ignore").merge(
    #     redirect_match, on="mbid", how="left"
    # )


    # #print(f"Direct matches:    {direct['title'].notna().sum():,}")
    # print(f"Redirect matches:  {redirect_match['title'].notna().sum():,}")

    # master_df = pd.concat([matched, redirect_matched], ignore_index=True)

    # print(f"\nFinal master_df: {len(master_df):,} rows")
    # print(f"with MB info: {master_df['title'].notna().sum():,}")
    # print(f"Without MB info: {master_df['title'].isna().sum():,}")


    # how="left" keeps all AcousticBrainz rows even if no MusicBrainz match

    del ab_df, mb_df

    # ── Save ───────────────────────────────────────────────────────────────────
    direct.to_parquet(MASTER_PATH, compression="snappy", index=False)
    print(f"Saved: {MASTER_PATH}")

print(f"\nMaster dataset: {len(direct):,} rows, {len(direct.columns)} columns")
# preview_candidates = [
#     "mbid",
#     "title",
#     "artist_name",  # MusicBrainz output uses artist_name
#     "release_year",
#     "bpm",
#     "danceability",
#     "mood_happy",
#     "genre",
# ]
# preview_cols = [c for c in preview_candidates if c in master_df.columns]
# missing_cols = [c for c in preview_candidates if c not in master_df.columns]

# if missing_cols:
#     print(f"Preview note: missing columns skipped -> {missing_cols}")

# print(master_df[preview_cols].head())