import pandas as pd
import os

# ── Config ────────────────────────────────────────────────────────────────────
INSPECT_DIR = "processed/inspect"
OUTPUT_DIR  = "processed"
MASTER_PATH = os.path.join(OUTPUT_DIR, "master_dataset.parquet")
MASTER_PATH_PARQUET = os.path.join(OUTPUT_DIR, "final_master_dataset.parquet")
MASTER_PATH_CSV = os.path.join(OUTPUT_DIR, "final_master_dataset.csv")

def read_csv(table_name: str, use_cols: list = None) -> pd.DataFrame:
    path = os.path.join(INSPECT_DIR, f"{table_name}.csv")
    print(f"  Reading '{table_name}.csv'...")
    df = pd.read_csv(path, usecols=use_cols, low_memory=False)
    print(f"    → {len(df):,} rows")
    return df


# ════════════════════════════════════════════════════════════════════════════════
# STEP 1: Load master (already has mbid, release_mbid, artist_mbid)
# ════════════════════════════════════════════════════════════════════════════════
print("\n[1] Loading master dataset...")
master_df = pd.read_parquet(MASTER_PATH).rename(columns = {'artist_mbids' : 'artist_mbid'})
print(f"    → {len(master_df):,} rows")
print(f"    Columns: {list(master_df.columns)}")

# Confirm the three key columns are present before proceeding
# for required in ["mbid", "release_mbid", "artist_mbid"]:
#     if required not in master_df.columns:
#         raise KeyError(f"Expected column '{required}' not found in master. "
#                        f"Available: {list(master_df.columns)}")


# ════════════════════════════════════════════════════════════════════════════════
# STEP 2: Release dates → join on release_mbid
#
# release.gid (= release_mbid) → release.release_group (int)
#   → release_group_meta.release_group_id → year/month/day
# ════════════════════════════════════════════════════════════════════════════════
print("\n[2] Building release date lookup...")
release_df = read_csv(
    "release", 
    use_cols=["gid", "release_group", "status", "language", "script", "quality"]
    )
release_df = release_df.rename(columns={"gid": "release_mbid"})

dates_df = read_csv(
    "release_group_meta",
    use_cols=["release_group_id", "release_year", "release_month", "release_day"]
)


release_dates_df = (
    release_df
    .merge(dates_df, left_on="release_group", right_on="release_group_id", how="left")
    .drop(columns=["release_group", "release_group_id"])
    #.drop_duplicates(subset="release_mbid")
)

# for col in ["release_year", "release_month", "release_day"]:
#     release_dates_df[col] = pd.to_numeric(
#         release_dates_df[col], errors="coerce"
#     ).astype("Int64")

print(f"    → {len(release_dates_df):,} rows")
del release_df, dates_df


# ════════════════════════════════════════════════════════════════════════════════
# STEP 3: Artist metadata → join on artist_mbid
#
# artist.gid (= artist_mbid) → artist.area (int) → area.id → area.name
# ════════════════════════════════════════════════════════════════════════════════
print("\n[3] Building artist metadata lookup...")
artist_df = read_csv(
    "artist",
    use_cols=["id", "gid", "name", "type", "area", "gender",
              "begin_date_year", "end_date_year", "ended"]
)


artist_df = artist_df.rename(columns={
    "gid":             "artist_mbid",
    "name":            "artist_name",
    "type":            "artist_type",
    "area":            "artist_area_id",
    "begin_date_year": "artist_begin_year",
    "end_date_year":   "artist_end_year",
})

area_df = read_csv("area", use_cols=["id", "name", "type"])


area_df  = area_df.rename(columns={"name": "artist_country",
                                   "type" : "artist_geo_entity",
                                   "id" : "area_id"})

print(area_df.columns)

print(artist_df.columns)
artist_df = (
    artist_df
    .merge(area_df, left_on="artist_area_id", right_on="area_id", how="left")
    .drop(columns=["artist_area_id", "area_id"])
)

print(f"    → {artist_df['artist_country'].notna().sum():,} artists with country")
del area_df


# ════════════════════════════════════════════════════════════════════════════════
# STEP 4: Genre lookups from all three tag sources
#
# release_group_tag  (album level  — richest)
# artist_tag         (artist level — fallback)
# recording_tag      (song level   — sparsest)
# ════════════════════════════════════════════════════════════════════════════════
print("\n[4] Building genre lookups...")

tag_df  = read_csv("tag", use_cols=["id", "name"])


tag_map = tag_df.set_index("id")["name"].to_dict()
del tag_df
print(f"    → {len(tag_map):,} unique tags loaded")


def build_genre_lookup(tag_csv: str, id_col: str,
                       mbid_map_df: pd.DataFrame,
                       int_col: str, mbid_col: str,
                       prefix: str) -> pd.DataFrame:
    
    df = read_csv(tag_csv, use_cols=[id_col, "tag", "count"])
    df = df[df['count'] > 0]
    df["tag_name"] = df["tag"].map(tag_map)
    df = df.dropna(subset=["tag_name"])

    top = (
        df.sort_values("count", ascending=False)
        .drop_duplicates(subset=id_col)
        [[id_col, "tag_name", "count"]]
        .rename(columns={"tag_name": f"{prefix}_top_genre",
                         "count":    f"{prefix}_top_genre_votes"})
    )
    all_tags = (
        df.sort_values("count", ascending=False)
        .groupby(id_col)["tag_name"]
        .apply("|".join)
        .reset_index()
        .rename(columns={"tag_name": f"{prefix}_all_genres"})
    )
    return (
        top.merge(all_tags, on=id_col, how="left")
        .merge(mbid_map_df[[int_col, mbid_col]],
               left_on=id_col, right_on=int_col, how="left")
        .drop(columns=[id_col, int_col])
        [[mbid_col, f"{prefix}_top_genre",
          f"{prefix}_top_genre_votes", f"{prefix}_all_genres"]]
    )


print("  Building release_group genre lookup...")
rg_id_df = (
    read_csv("release", use_cols=["gid", "release_group"])
    .rename(columns={"gid": "release_mbid"})
    .drop_duplicates(subset="release_group")
)


release_genre_df = build_genre_lookup(
    "release_group_tag", "release_group",
    rg_id_df, "release_group", "release_mbid", "release_group"
)



print(f"    → {len(release_genre_df):,} releases with genre tags")
del rg_id_df

print("  Building artist genre lookup...")
artist_genre_df = build_genre_lookup(
    "artist_tag", "artist",
    artist_df[["id", "artist_mbid"]], "id", "artist_mbid", "artist"
)


print(f"    → {len(artist_genre_df):,} artists with genre tags")
artist_df = artist_df.drop(columns=["id"])

print("  Building recording genre lookup...")
recording_id_df = (
    read_csv("recording", use_cols=["id", "gid", "length", "video"])
    .rename(columns={"gid": "mbid"})
)


recording_genre_df = build_genre_lookup(
    "recording_tag", "recording",
    recording_id_df, "id", "mbid", "recording"
)


print(f"    → {len(recording_genre_df):,} recordings with genre tags")
del recording_id_df


# ════════════════════════════════════════════════════════════════════════════════
# STEP 5: Join everything onto master (all LEFT — NAs are fine)
# ════════════════════════════════════════════════════════════════════════════════
print("\n[5] Joining onto master dataset...")
print(f"    Rows before: {len(master_df):,}")



# Drop stale columns from any previous run of this script
stale = [
    "release_year", "release_month", "release_day",
    "artist_name", "artist_type", "artist_country", "gender",
    "artist_begin_year", "artist_end_year", "ended",
    "release_group_top_genre", "release_group_top_genre_votes", "release_group_all_genres",
    "artist_top_genre", "artist_top_genre_votes", "artist_all_genres",
    "recording_top_genre", "recording_top_genre_votes", "recording_all_genres",
    "genre",
]
cols_to_drop = [c for c in stale if c in master_df.columns]
if cols_to_drop:
    print(f"    Dropping stale columns: {cols_to_drop}")
    master_df = master_df.drop(columns=cols_to_drop)

master_df = master_df.merge(release_dates_df,  on="release_mbid", how="left")
print(f"    After release dates:   {master_df['release_year'].notna().sum():,} with year")

master_df = master_df.merge(
    artist_df[["artist_mbid", "artist_name", "artist_type",
               "artist_country", "gender", "artist_geo_entity",
               "artist_begin_year", "artist_end_year", "ended"]],
    on="artist_mbid", how="left"
)





print(f"    After artist:          {master_df['artist_country'].notna().sum():,} with country")

master_df = master_df.merge(release_genre_df,   on="release_mbid", how="left")
print(f"    After release genre:   {master_df['release_group_top_genre'].notna().sum():,} with release genre")

master_df = master_df.merge(artist_genre_df,    on="artist_mbid",  how="left")
print(f"    After artist genre:    {master_df['artist_top_genre'].notna().sum():,} with artist genre")

master_df = master_df.merge(recording_genre_df, on="mbid",         how="left")
print(f"    After recording genre: {master_df['recording_top_genre'].notna().sum():,} with recording genre")

print(f"    Rows after:  {len(master_df):,}  (should match before)")


# ════════════════════════════════════════════════════════════════════════════════
# STEP 6: Single priority genre column
# Priority: release_group (richest) → artist → recording (sparsest)
# ════════════════════════════════════════════════════════════════════════════════
print("\n[6] Building priority genre column...")
master_df["genre"] = (
    master_df["release_group_top_genre"]
    .fillna(master_df["artist_top_genre"])
    .fillna(master_df["recording_top_genre"])
)
coverage = master_df["genre"].notna().mean() * 100
print(f"    Coverage: {master_df['genre'].notna().sum():,} / {len(master_df):,} ({coverage:.1f}%)")


# ════════════════════════════════════════════════════════════════════════════════
# STEP 7: Save
# ════════════════════════════════════════════════════════════════════════════════
print(f"\n[7] Saving to {MASTER_PATH}...")
master_df.to_parquet(MASTER_PATH_PARQUET, compression="snappy", index=False)
print("    Done.")

master_df.to_csv(MASTER_PATH_CSV, index=False)
print(" Done save as csv")

# ── Preview ───────────────────────────────────────────────────────────────────
print("\n── Sample ───────────────────────────────────────────────────────────────")
preview_cols = ["mbid", "release_mbid", "artist_mbid", "release_year",
                "artist_country", "artist_type", "gender", "genre",
                "release_group_top_genre", "artist_top_genre", "recording_top_genre"]
print(master_df[[c for c in preview_cols if c in master_df.columns]].head(10).to_string())

print("\n── Null counts ──────────────────────────────────────────────────────────")
check_cols = ["release_year", "release_month", "release_day",
              "artist_name", "artist_type", "artist_country", "gender",
              "artist_begin_year", "artist_end_year",
              "genre", "release_group_top_genre",
              "artist_top_genre", "recording_top_genre"]
null_counts = master_df[[c for c in check_cols if c in master_df.columns]].isnull().sum()
null_pct    = (null_counts / len(master_df) * 100).round(1)
print(pd.DataFrame({"null_count": null_counts, "null_%": null_pct}).to_string())
