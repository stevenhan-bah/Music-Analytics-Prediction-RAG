import pandas as pd
import os

OUTPUT_DIR = "processed"
MB_PATH    = os.path.join(OUTPUT_DIR, "musicbrainz_canonical.parquet")

if os.path.exists(MB_PATH):
    print(f"Cached file found — loading from {MB_PATH}...")
    mb_df = pd.read_parquet(MB_PATH)
    print(f"Loaded: {len(mb_df):,} rows")

else:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    DATA_DIR = "data"  # wherever you extracted the 3 CSVs

    # ── Validate files exist ───────────────────────────────────────────────────
    expected = [
        "canonical_musicbrainz_data.csv"#,
        #"canonical_recording_redirect.csv",
        #"canonical_release_redirect.csv",
    ]
    missing = [f for f in expected
               if not os.path.exists(os.path.join(DATA_DIR, f))]
    if missing:
        raise FileNotFoundError(f"Missing in {DATA_DIR}/: {missing}")
    print("All files found.")

    # ── Load canonical_musicbrainz_data.csv — the main one ────────────────────
    print("Loading canonical_musicbrainz_data.csv (this is large, may take a while)...")
    canon_df = pd.read_csv(
        os.path.join(DATA_DIR, "canonical_musicbrainz_data.csv"),
        usecols=[                          # only load columns you need
            "recording_mbid",
            "recording_name",
            "combined_lookup",
            "artist_credit_name",
            "artist_mbids",
            "release_mbid",
            "release_name",
        ]
    )
    print(f"  → {len(canon_df):,} rows")

    # ── Load canonical_recording_redirect.csv ─────────────────────────────────
    # Maps non-canonical recording MBIDs → canonical ones
    # Useful so AcousticBrainz MBIDs that aren't "canonical" still get matched
    # print("Loading canonical_recording_redirect.csv...")
    # recording_redirect_df = pd.read_csv(
    #     os.path.join(DATA_DIR, "canonical_recording_redirect.csv"),
    #     usecols=["recording_mbid", "canonical_recording_mbid"]
    # )
    # print(f"  → {len(recording_redirect_df):,} rows")

    # ── Load canonical_release_redirect.csv ───────────────────────────────────
    # Maps non-canonical release MBIDs → canonical ones
    # print("Loading canonical_release_redirect.csv...")
    # release_redirect_df = pd.read_csv(
    #     os.path.join(DATA_DIR, "canonical_release_redirect.csv"),
    #     usecols=["release_mbid", "canonical_release_mbid", "release_group_mbid"]
    # )
    # print(f"  → {len(release_redirect_df):,} rows")

    # ── Rename columns to match your existing pipeline ────────────────────────
    mb_df = canon_df.rename(columns={
        "recording_mbid":    "mbid"#,
        # "recording_name":    "title",
        # "artist_credit_name": "artist_name",
        # "release_name":      "album_name",
    })
    del canon_df

    # ── Deduplicate ───────────────────────────────────────────────────────────
    # mb_df = mb_df.drop_duplicates(subset="mbid", keep="first")
    # print(f"\nAfter dedup: {len(mb_df):,} unique recordings")

    # ── Save ──────────────────────────────────────────────────────────────────
    mb_df.to_parquet(MB_PATH, compression="snappy", index=False)
    print(f"Saved: {MB_PATH}")

print(f"\nColumns: {list(mb_df.columns)}")
# preview_candidates = ["mbid", "title", "artist_name", "album_name"]
# preview_cols = [c for c in preview_candidates if c in mb_df.columns]
# missing_cols = [c for c in preview_candidates if c not in mb_df.columns]

# if missing_cols:
#     print(f"Preview note: missing columns skipped -> {missing_cols}")

# print(mb_df[preview_cols].head(10))