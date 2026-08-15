import duckdb
import pandas as pd
import streamlit as st


DB_PATH = "notebook/RAG_data/music.db"

# Cache resource to create one DuckDB connection per Streamlit session
@st.cache_resource
def get_connection():
    """
    Creates one DuckDB connection per Streamlit session.
    """
    return duckdb.connect(DB_PATH, read_only=True) # read_only=True to prevent modifications to the database

# Cache the query results to get the list of artists from the database
@st.cache_data
def get_artists():

    con = get_connection()

    query = """
    SELECT DISTINCT artist_name
    FROM music
    WHERE artist_name IS NOT NULL
    ORDER BY artist_name
    """

    return con.execute(query).df()["artist_name"].tolist() # Convert the result to a list of artist names

# Cache the query results 
@st.cache_data
def get_artist_data(artist_name):

    con = get_connection()

    # ? is a placeholder for the artist name
    query = """
    SELECT *
    FROM music
    WHERE artist_name = ?
    ORDER BY release_year
    """

    return con.execute(query, [artist_name]).df()

# Cache the query results to get the summary data for an artist
@st.cache_data
def get_artist_summary(artist_name):

    con = get_connection()

    query = """
    SELECT
        AVG(bpm) AS bpm,
        AVG(danceability) AS danceability,
        AVG(average_loudness) AS average_loudness,
        AVG(mood_happy_prob) AS mood_happy_prob,
        AVG(mood_aggressive_prob) AS mood_aggressive_prob
    FROM music
    WHERE artist_name = ?
    """

    return con.execute(query, [artist_name]).df()


# Cache the query results to get the feature trend for an artist
@st.cache_data
def get_artist_feature_trend(
    artist_name,
    feature
):

    con = get_connection()

    allowed_features = {
        "bpm",
        "danceability",
        "average_loudness",
        "mood_happy_prob",
        "mood_aggressive_prob",
        "onset_rate",
        "dynamic_complexity",
        "key_scale",
        "mood_happy",
        "mood_sad",
        "mood_relaxed",
        "mood_aggressive",
        "mood_acoustic",
        "mood_electronic",
        "mood_party",
        "timbre",
        "tonal_atonal",
    }

    if feature not in allowed_features:
        raise ValueError("Invalid feature selected.")

    # Group by release year and calculate the average value of the feature
    query = f"""
    SELECT
        release_year,
        AVG({feature}) AS value
    FROM music
    WHERE artist_name = ?
    GROUP BY release_year
    ORDER BY release_year
    """

    return con.execute(query, [artist_name]).df()

## Temporal trends

# Cache the query results to get the average loudness by decade
@st.cache_data
def get_loudness_by_decade():

    con = get_connection()

    query = """
    SELECT
        FLOOR(release_year/10)*10 AS decade,
        AVG(average_loudness) AS average_loudness
    FROM music
    WHERE release_year IS NOT NULL
    GROUP BY decade
    ORDER BY decade
    """

    return con.execute(query).df()


## Two feature comparison

# Cache the query results to get the trend of two features over time
@st.cache_data
def get_two_feature_trend(
    feature1,
    feature2
):

    con = get_connection()

    allowed = {
        "bpm",
        "danceability",
        "average_loudness",
        "mood_happy_prob",
        "mood_aggressive_prob",
        "onset_rate",
        "dynamic_complexity",
        "key_scale",
        "mood_happy",
        "mood_sad",
        "mood_relaxed",
        "mood_aggressive",
        "mood_acoustic",
        "mood_electronic",
        "mood_party",
        "timbre",
        "tonal_atonal",
    }

    if feature1 not in allowed or feature2 not in allowed:
        raise ValueError("Invalid feature selected.")

    query = f"""
    SELECT

        FLOOR(release_year/10)*10 AS decade,

        AVG({feature1}) AS {feature1},

        AVG({feature2}) AS {feature2}

    FROM music

    GROUP BY decade

    ORDER BY decade
    """

    return con.execute(query).df()


## Genres

# Cache the query results to get the list of genres from the database
@st.cache_data
def get_genres():

    con = get_connection()

    query = """
    SELECT DISTINCT main_genre
    FROM music
    ORDER BY main_genre
    """

    return con.execute(query).df()["main_genre"].tolist()


## Genre comparison

# Cache the query results to get the comparison data for a list of genres
@st.cache_data
def get_genre_comparison(selected_genres):

    con = get_connection()

    # Create a string of placeholders for the genres
    placeholders = ",".join(["?"] * len(selected_genres))

    query = f"""
    SELECT

        main_genre,

        AVG(bpm) AS bpm,

        AVG(bpm_histogram_first_peak_bpm_mean)
            AS bpm_histogram_first_peak_bpm_mean,

        AVG(bpm_histogram_first_peak_bpm_median)
            AS bpm_histogram_first_peak_bpm_median,

        AVG(bpm_histogram_second_peak_bpm_mean)
            AS bpm_histogram_second_peak_bpm_mean,

        AVG(bpm_histogram_second_peak_bpm_median)
            AS bpm_histogram_second_peak_bpm_median,

        AVG(danceability) AS danceability,

        AVG(average_loudness) AS average_loudness,

        AVG(mood_happy_prob) AS mood_happy_prob,

        AVG(mood_aggressive_prob) AS mood_aggressive_prob,

        AVG(onset_rate) AS onset_rate,

        AVG(dynamic_complexity) AS dynamic_complexity

    FROM music

    WHERE main_genre IN ({placeholders})

    GROUP BY main_genre

    ORDER BY main_genre
    """

    return con.execute(query, selected_genres).df()


# Cache the query results to search for artists
@st.cache_data
def search_artists(search_term):

    con = get_connection()

    query = """
    SELECT DISTINCT artist_name

    FROM music

    WHERE LOWER(artist_name)
          LIKE LOWER(?)

    ORDER BY artist_name

    LIMIT 25
    """

    # % is a wildcard for any sequence of characters
    result = con.execute(
        query,
        [f"%{search_term}%"]
    ).df()


    return result["artist_name"].tolist()


