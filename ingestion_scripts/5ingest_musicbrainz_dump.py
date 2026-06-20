import tarfile
import pandas as pd
import os
import difflib

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR     = "data"
OUTPUT_DIR   = "processed/inspect"
MBDUMP_PATH  = os.path.join(DATA_DIR, "mbdump.tar.bz2")
DERIVED_PATH = os.path.join(DATA_DIR, "mbdump-derived.tar.bz2")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Helper (reused from your existing code) ───────────────────────────────────
def read_tsv_from_tar(tar_path: str, table_name: str,
                      col_names: list, use_cols: list = None) -> pd.DataFrame:
    use_cols = use_cols or col_names
    print(f"  Reading '{table_name}' from {os.path.basename(tar_path)}...")
    with tarfile.open(tar_path, "r:bz2") as tar:
        member_name = f"mbdump/{table_name}"
        if member_name not in tar.getnames():
            available = [n.split("/", 1)[1] for n in tar.getnames() if n.startswith("mbdump/")]
            guesses = difflib.get_close_matches(table_name, available, n=5, cutoff=0.3)
            raise KeyError(f"'{table_name}' not found. Closest: {guesses}")
        f = tar.extractfile(member_name)
        df = pd.read_csv(
            f, sep="\t", header=None,
            names=col_names, usecols=use_cols,
            na_values=["\\N"], low_memory=False,
        )
    print(f"    → {len(df):,} rows, {len(df.columns)} columns")
    return df


# ════════════════════════════════════════════════════════════════════════════════
# mbdump.tar.bz2  — core catalog tables
# ════════════════════════════════════════════════════════════════════════════════

# ── 1. recording ──────────────────────────────────────────────────────────────
# KEY: gid = recording_mbid  ← this is the mbid that links to AcousticBrainz
# artist_credit is an integer FK → artist_credit table (not artist.gid directly)
# length is in milliseconds
recording_df = read_tsv_from_tar(
    MBDUMP_PATH,
    table_name = "recording",
    col_names  = ["id", "gid", "name", "artist_credit",
                  "length", "comment", "edits_pending",
                  "last_updated", "video"],
    use_cols   = ["id", "gid", "name", "artist_credit", "length", "comment", "video"],
)
recording_df.to_csv(os.path.join(OUTPUT_DIR, "recording.csv"), index=False)
# id         = internal integer id (used as FK in other tables)
# gid        = recording_mbid ← JOIN KEY to AcousticBrainz
# name       = song title
# length     = duration in milliseconds
# video      = boolean, True if this is a video recording
print("  Saved: recording.csv\n")


# ── 2. release ────────────────────────────────────────────────────────────────
# KEY: gid = release_mbid  ← links to canonical_musicbrainz_data.csv release_mbid
# release_group is integer FK → release_group table
release_df = read_tsv_from_tar(
    MBDUMP_PATH,
    table_name = "release",
    col_names  = ["id", "gid", "name", "artist_credit", "release_group",
                  "status", "packaging", "language", "script", "barcode",
                  "comment", "edits_pending", "quality", "last_updated"],
    use_cols   = ["id", "gid", "name", "artist_credit", "release_group",
                  "status", "language", "script", "barcode", "quality"],
)
release_df.to_csv(os.path.join(OUTPUT_DIR, "release.csv"), index=False)
# id             = internal integer id
# gid            = release_mbid ← JOIN KEY to canonical CSV
# name           = album/release title
# release_group  = integer FK → release_group.id
# status         = 1=Official, 2=Promotional, 3=Bootleg, 4=Pseudo-release
# language       = ISO 639-3 language code of the release (e.g. "eng")
# script         = writing script (e.g. "Latn", "Cyrl", "Hani")
# barcode        = physical barcode if present
# quality        = data quality: -1=Unknown, 0=Low, 1=Normal, 2=High
print("  Saved: release.csv\n")


# ── 3. release_group ─────────────────────────────────────────────────────────
# KEY: gid = release_group_mbid
# type: 1=Album, 2=Single, 3=EP, 4=Other, 5=Broadcast, 6=Compilation, etc.
release_group_df = read_tsv_from_tar(
    MBDUMP_PATH,
    table_name = "release_group",
    col_names  = ["id", "gid", "name", "artist_credit",
                  "type", "edits_pending", "last_updated", "comment"],
    use_cols   = ["id", "gid", "name", "artist_credit", "type", "comment"],
)
release_group_df.to_csv(os.path.join(OUTPUT_DIR, "release_group.csv"), index=False)
# id    = internal integer id (FK in release.release_group)
# gid   = release_group_mbid
# name  = album/group title
# type  = 1=Album, 2=Single, 3=EP, 4=Other, 5=Broadcast, 6=Compilation,
#         7=DJ-mix, 8=Mixtape/Street, 9=Demo, 10=Live, 11=Remix, 12=Soundtrack
print("  Saved: release_group.csv\n")


# ── 4. artist ────────────────────────────────────────────────────────────────
# KEY: gid = artist_mbid  ← links to canonical_musicbrainz_data.csv artist_mbids
# area/begin_area/end_area are integer FKs → area table
artist_df = read_tsv_from_tar(
    MBDUMP_PATH,
    table_name = "artist",
    col_names  = ["id", "gid", "name", "sort_name",
                  "begin_date_year", "begin_date_month", "begin_date_day",
                  "end_date_year", "end_date_month", "end_date_day",
                  "type", "area", "gender", "comment",
                  "edits_pending", "last_updated", "ended",
                  "begin_area", "end_area"],
    use_cols   = ["id", "gid", "name", "sort_name",
                  "begin_date_year", "begin_date_month", "begin_date_day",
                  "end_date_year", "end_date_month", "end_date_day",
                  "type", "area", "gender", "ended"],
)
artist_df.to_csv(os.path.join(OUTPUT_DIR, "artist.csv"), index=False)
# id               = internal integer id
# gid              = artist_mbid ← JOIN KEY to canonical CSV artist_mbids
# name             = artist display name
# sort_name        = name for sorting (e.g. "Beatles, The")
# begin_date_year  = year artist/band formed or person born
# end_date_year    = year artist/band disbanded or person died
# type             = 1=Person, 2=Group, 3=Orchestra, 4=Choir, 5=Character, 6=Other
# area             = integer FK → area.id (home country/region)
# gender           = 1=Male, 2=Female, 3=Other, 4=Not applicable
# ended            = boolean, True if artist is no longer active
print("  Saved: artist.csv\n")


# ── 5. area ──────────────────────────────────────────────────────────────────
# Lookup table: integer area id → country/region name
# Used to decode artist.area into a human-readable country
area_df = read_tsv_from_tar(
    MBDUMP_PATH,
    table_name = "area",
    col_names  = ["id", "gid", "name", "type", "edits_pending",
                  "last_updated", "begin_date_year", "begin_date_month",
                  "begin_date_day", "end_date_year", "end_date_month",
                  "end_date_day", "ended", "comment"],
    use_cols   = ["id", "gid", "name", "type"],
)
area_df.to_csv(os.path.join(OUTPUT_DIR, "area.csv"), index=False)
# id   = integer id (FK target from artist.area, release country tables)
# gid  = area_mbid
# name = country/region name (e.g. "United States", "United Kingdom")
# type = 1=Country, 2=Subdivision, 3=County, 4=Municipality, 5=City, 6=District, 7=Island
print("  Saved: area.csv\n")


# ════════════════════════════════════════════════════════════════════════════════
# mbdump-derived.tar.bz2  — tags, ratings, release dates
# ════════════════════════════════════════════════════════════════════════════════

# ── 6. release_group_meta ─────────────────────────────────────────────────────
# KEY: release_group_id = integer FK → release_group.id
# Contains the earliest known release date for an album/group
# This is the best source for "when was this song first released"
dates_df = read_tsv_from_tar(
    DERIVED_PATH,
    table_name = "release_group_meta",
    col_names  = ["release_group_id", "release_count",
                  "release_year", "release_month", "release_day",
                  "last_release_year", "last_release_month"],
    use_cols   = ["release_group_id", "release_count",
                  "release_year", "release_month", "release_day",
                  "last_release_year", "last_release_month"],
)
dates_df.to_csv(os.path.join(OUTPUT_DIR, "release_group_meta.csv"), index=False)
# release_group_id  = integer FK → release_group.id
# release_count     = number of releases in this release group
# release_year      = year of first/earliest release ← KEY for era prediction
# release_month     = month of first release
# release_day       = day of first release
# last_release_year = most recent re-release year (useful for spotting remasters)
print("  Saved: release_group_meta.csv\n")


# ── 7. tag ───────────────────────────────────────────────────────────────────
# Master lookup of all tags (genres, moods, descriptors)
# e.g. "rock", "jazz", "90s", "female vocalist", "british"
tag_df = read_tsv_from_tar(
    DERIVED_PATH,
    table_name = "tag",
    col_names  = ["id", "name", "ref_count"],
    use_cols   = ["id", "name", "ref_count"],
)
tag_df.to_csv(os.path.join(OUTPUT_DIR, "tag.csv"), index=False)
# id        = integer tag id (FK target from *_tag tables below)
# name      = tag string (e.g. "jazz", "rock", "hip hop", "1990s")
# ref_count = total number of times this tag has been applied across all entities
print("  Saved: tag.csv\n")


# ── 8. recording_tag ─────────────────────────────────────────────────────────
# Genre/tag votes at the individual SONG level
# recording → tag with a vote count (higher = more users applied this tag)
# NOTE: recording here is integer id (recording.id), NOT the gid/mbid
recording_tag_df = read_tsv_from_tar(
    DERIVED_PATH,
    table_name = "recording_tag",
    col_names  = ["recording", "tag", "count", "last_updated"],
    use_cols   = ["recording", "tag", "count"],
)
recording_tag_df.to_csv(os.path.join(OUTPUT_DIR, "recording_tag.csv"), index=False)
# recording = integer FK → recording.id  (join to recording.id, then use recording.gid as mbid)
# tag       = integer FK → tag.id        (join to tag.name for the genre string)
# count     = number of users who applied this tag to this recording
print("  Saved: recording_tag.csv\n")


# ── 9. artist_tag ─────────────────────────────────────────────────────────────
# Genre/tag votes at the ARTIST level
# Often more complete than recording-level tags — good fallback for genre
artist_tag_df = read_tsv_from_tar(
    DERIVED_PATH,
    table_name = "artist_tag",
    col_names  = ["artist", "tag", "count", "last_updated"],
    use_cols   = ["artist", "tag", "count"],
)
artist_tag_df.to_csv(os.path.join(OUTPUT_DIR, "artist_tag.csv"), index=False)
# artist = integer FK → artist.id  (join to artist.id, then use artist.gid as artist_mbid)
# tag    = integer FK → tag.id
# count  = vote count
print("  Saved: artist_tag.csv\n")


# ── 10. release_group_tag ─────────────────────────────────────────────────────
# Genre/tag votes at the ALBUM level
# Often the richest source of genre tags — albums get tagged more than songs
release_group_tag_df = read_tsv_from_tar(
    DERIVED_PATH,
    table_name = "release_group_tag",
    col_names  = ["release_group", "tag", "count", "last_updated"],
    use_cols   = ["release_group", "tag", "count"],
)
release_group_tag_df.to_csv(os.path.join(OUTPUT_DIR, "release_group_tag.csv"), index=False)
# release_group = integer FK → release_group.id
# tag           = integer FK → tag.id
# count         = vote count
print("  Saved: release_group_tag.csv\n")


# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 60)
print(f"All files saved to: {OUTPUT_DIR}/")
print()
print("KEY IDENTIFIER SUMMARY")
print("-" * 60)
print("recording.gid          → recording_mbid (= AcousticBrainz mbid)")
print("release.gid            → release_mbid   (= canonical CSV release_mbid)")
print("artist.gid             → artist_mbid    (= canonical CSV artist_mbids)")
print("release_group.id       → FK from release.release_group")
print("area.id                → FK from artist.area")
print("recording_tag.recording → FK to recording.id  (integer, not gid)")
print("artist_tag.artist       → FK to artist.id     (integer, not gid)")
print("release_group_tag.*     → FK to release_group.id")
print("tag.id                  → FK from all *_tag tables")