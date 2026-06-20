import pandas as pd
import tarfile
import json
import zstandard as zstd  # pip install zstandard
import os
import glob

OUTPUT_DIR = "processed"
MERGED_PARQUET_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_merged.parquet")
MERGED_CSV_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_merged.csv")
FULL_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_full.parquet")

DUPLICATES_CSV_PATH = os.path.join(OUTPUT_DIR, "acousticbrainz_before_dedup.csv")

if os.path.exists(FULL_PATH):
    df_final=pd.read_parquet(FULL_PATH)
    print(f"Loaded: {len(df_final):,}")

else:

    if os.path.exists(MERGED_PARQUET_PATH):
        print(f"Loading base data from {MERGED_PARQUET_PATH}...")
        df = pd.read_parquet(MERGED_PARQUET_PATH)
    elif os.path.exists(MERGED_CSV_PATH):
        print(f"Loading base data from {MERGED_CSV_PATH}...")
        df = pd.read_csv(MERGED_CSV_PATH)
    else:
        raise FileNotFoundError(
            f"could not find {MERGED_PARQUET_PATH} or {MERGED_CSV_PATH}"
        )

    # ── 2. Parse a single high-level JSON file ────────────────────────────────────
    def parse_highlevel_json(data: bytes) -> dict | None:
        """Extract mood and genre fields from one high-level JSON blob."""
        try:
            doc = json.loads(data)
            hl  = doc.get("highlevel", {})

            # Helper: safely get the most likely value + probability
            def get_value(field):
                return hl.get(field, {}).get("value", None)

            def get_prob(field):
                probs = hl.get(field, {}).get("all", {})
                val   = get_value(field)
                return probs.get(val, None) if val else None

            return {
                "mbid": doc["metadata"]["tags"]["musicbrainz_recordingid"][0],

                # Mood
                "mood_happy":       get_value("mood_happy"),
                "mood_sad":         get_value("mood_sad"),
                "mood_relaxed":     get_value("mood_relaxed"),
                "mood_aggressive":  get_value("mood_aggressive"),
                "mood_acoustic":    get_value("mood_acoustic"),
                "mood_electronic":  get_value("mood_electronic"),
                "mood_party":       get_value("mood_party"),

                # Mood probabilities (confidence scores 0–1)
                "mood_happy_prob":      get_prob("mood_happy"),
                "mood_aggressive_prob": get_prob("mood_aggressive"),

                # Genre
                "genre":            get_value("genre_rosamerica"),

                # Other high-level
                "voice_gender":     get_value("gender"),
                "timbre":           get_value("timbre"),
                "tonal_atonal":     get_value("tonal_atonal"),
                "voice_instrumental": get_value("voice_instrumental"),
            }
        except Exception:
            return None  # skip malformed files

    # ── 3. Extract all records from one .zst dump file ───────────────────────────
    def extract_highlevel_dump(zst_path: str) -> pd.DataFrame:
        """Stream through a .zst tar archive and parse every JSON inside."""
        records = []

        # Open the .zst stream
        with open(zst_path, "rb") as fh:
            dctx   = zstd.ZstdDecompressor()
            stream = dctx.stream_reader(fh)

            # Wrap in tarfile (the .zst contains a .tar)
            with tarfile.open(fileobj=stream, mode="r|") as tar:
                for i, member in enumerate(tar):
                    if not member.name.endswith(".json"):
                        continue

                    f    = tar.extractfile(member)
                    if f is None:
                        continue

                    row = parse_highlevel_json(f.read())
                    if row:
                        records.append(row)

                    # Progress update every 100k files
                    if (i + 1) % 100_000 == 0:
                        print(f"  {zst_path}: processed {i+1:,} files...")

        return pd.DataFrame(records)

    # ── 4. Process all .tar.zst dump files in data/ and combine ───────────────────
    zst_files = sorted(glob.glob(os.path.join("data", "**", "*.tar.zst"), recursive=True))

    if not zst_files:
        raise FileNotFoundError("No .tar.zst files found under data/")
    else:
        print(f"Found {len(zst_files)} dump file(s): {zst_files}")
        hl_chunks = []

        for path in zst_files:
            print(f"\nProcessing {path}...")
            chunk = extract_highlevel_dump(path)
            print(f"  → {len(chunk):,} records extracted")
            hl_chunks.append(chunk)

        highlevel_df = pd.concat(hl_chunks, ignore_index=True)



        highlevel_df.to_csv(DUPLICATES_CSV_PATH, index = False)

        # print(f"high-level data total (with duplicates): {len(highlevel_df):,} tracks")

        # os.makedirs(OUTPUT_DIR, exist_ok=True)
        # highlevel_df['is_duplicate'] = 




        # Drop duplicate mbids (some tracks have multiple submissions)
        highlevel_df = highlevel_df.drop_duplicates(subset="mbid", keep="first")
        print(f"\nHigh-level data total: {len(highlevel_df):,} unique tracks")

    # ── 5. Merge high-level into your existing dataframe ─────────────────────────
    df = df.drop_duplicates(subset="mbid", keep="first")
    df_final = df.merge(highlevel_df, on="mbid", how="left", validate="one_to_one")

    print(f"\nFinal merged dataframe: {len(df_final):,} rows")
    print(f"Columns: {list(df_final.columns)}")
    print(df_final[["mbid", "bpm", "danceability", "mood_happy", "genre"]].head())

    # ── 6. Save to Parquet for S3/Athena ─────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_final.to_parquet(FULL_PATH, compression="snappy", index=False)
    print(f"\nSaved: {FULL_PATH}")
