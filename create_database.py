# Create a DuckDB database from the parquet file

import duckdb
from pathlib import Path

# Paths
PARQUET_FILE = "notebook/RAG_data/new_music_data_for_analytics.parquet"
DB_FILE = "notebook/RAG_data/music.db"

# Remove the database if it already exists
Path(DB_FILE).unlink(missing_ok=True)

# Connect (creates the database file if it doesn't exist)
con = duckdb.connect(DB_FILE)

print("Creating database...")

# Create the table from the parquet file
con.execute(f"""
CREATE TABLE music AS
SELECT *
FROM read_parquet('{PARQUET_FILE}');
""")

# Check the row count
rows = con.execute("SELECT COUNT(*) FROM music").fetchone()[0] # fetchone() returns a tuple, so we need to access the first element
print(f"Imported {rows} rows.")

# Describe the columns in the schema
print("\nColumns:")
print(con.execute("DESCRIBE music").fetchdf()) # fetchdf() returns a pandas DataFrame

# close the connection
con.close()

print(f"\nDatabase saved to: {DB_FILE}")