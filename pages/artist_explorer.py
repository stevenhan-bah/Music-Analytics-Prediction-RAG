# Artist Explorer page

import streamlit as st
import altair as alt # Import altair visulaization library, creates charts from dataframes

from config import FEATURE_OPTIONS

from database import (
    search_artists,
    get_artist_data,
    get_artist_feature_trend,
)

def show():
    st.title("Artist Explorer")

    # Create a text box for the user to search for an artist
    artist_search = st.text_input(
        "Search for an artist"
    )

    # If the user has entered an artist name, search for artists that match the name
    if artist_search:

        matches = search_artists(
            artist_search
        )

        if matches:

            selected_artist = st.selectbox(
                "Select artist",
                matches
            )

        else:
            st.warning(
                "No artists found."
            )
            return

    else:
        st.info(
            "Start typing an artist name."
        )
        return

    # Load the artist data from the database
    artist_data = get_artist_data(selected_artist)

    st.write(
        f"Selected artist: {selected_artist}"
    )

    if artist_data.empty:
        st.warning("No songs found.")
        return

    # Statistics
    st.subheader(selected_artist)

    cols = [
        "bpm",
        "danceability",
        "average_loudness",
        "mood_happy_prob",
        "mood_aggressive_prob",
    ]

    # Display the statistics as an interactive table
    st.dataframe(
        artist_data[cols].describe(),
        use_container_width=True,
    )

    # Feature Selector
    feature = st.selectbox(
        "Select a feature",
        FEATURE_OPTIONS,
    )

    # Query DuckDB
    trend = get_artist_feature_trend(
        selected_artist,
        feature,
    )

    # Altair Chart
    chart = (
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "release_year:O", # O means ordinal, a categorical variable
                title="Release Year",
            ),
            y=alt.Y(
                "value:Q", # Q means quantitative, a numerical variable
                title=feature,
            ),
            tooltip=[
                "release_year",
                "value",
            ],
        )
        .properties(
            width=900,
            height=450,
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True, # expands to fit the container width
    )