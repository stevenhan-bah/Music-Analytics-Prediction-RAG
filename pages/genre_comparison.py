# Genre Comparison page

import streamlit as st
import altair as alt

from database import (
    get_genres,
    get_genre_comparison,
)

def show():

    st.title("Genre Comparison")

    genres = get_genres()

    selected_genres = st.multiselect(
        "Select genres",
        genres,
        default=genres[:3]
    )

    if not selected_genres:
        st.warning("Please select at least one genre.")
        return

    genre_data = get_genre_comparison(selected_genres)


    st.subheader("Compare BPM Histogram Peaks")

    bpm_features = [
        "bpm",
        "bpm_histogram_first_peak_bpm_mean",
        "bpm_histogram_first_peak_bpm_median",
        "bpm_histogram_second_peak_bpm_mean",
        "bpm_histogram_second_peak_bpm_median",
    ]

    bpm_labels = {
        "bpm": "BPM",
        "bpm_histogram_first_peak_bpm_mean": "First Peak Mean",
        "bpm_histogram_first_peak_bpm_median": "First Peak Median",
        "bpm_histogram_second_peak_bpm_mean": "Second Peak Mean",
        "bpm_histogram_second_peak_bpm_median": "Second Peak Median",
    }

    bpm_df = genre_data[
        ["main_genre"] + bpm_features
    ].melt(
        id_vars="main_genre",
        var_name="Feature",
        value_name="Value",
    )

    # Replace the feature names with the labels
    bpm_df["Feature"] = bpm_df["Feature"].replace(
        bpm_labels
    )


    chart = (
        alt.Chart(bpm_df)
        .mark_bar()
        .encode(
            x="main_genre:N",
            y="Value:Q",
            color="main_genre:N",
            column="Feature:N",
            tooltip=[
                "main_genre",
                "Feature",
                "Value",
            ],
        )
        .properties(
            width=180
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


    st.subheader(
        "Danceability, Loudness and Mood"
    )

    mood_features = [
        "danceability",
        "average_loudness",
        "mood_happy_prob",
        "mood_aggressive_prob",
    ]

    mood_df = genre_data[
        ["main_genre"] + mood_features
    ].melt(
        id_vars="main_genre",
        var_name="Feature",
        value_name="Value",
    )

    chart = (
        alt.Chart(mood_df)
        .mark_bar()
        .encode(
            x="main_genre:N",
            y="Value:Q",
            color="main_genre:N",
            column="Feature:N",
            tooltip=[
                "main_genre",
                "Feature",
                "Value",
            ],
        )
        .properties(
            width=180
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


    st.subheader(
        "Dynamic Complexity & Onset Rate"
    )

    complexity = genre_data[
        [
            "main_genre",
            "onset_rate",
            "dynamic_complexity",
        ]
    ].melt(
        id_vars="main_genre",
        var_name="Feature",
        value_name="Value",
    )

    chart = (
        alt.Chart(complexity)
        .mark_bar()
        .encode(
            x="main_genre:N",
            y="Value:Q",
            color="main_genre:N",
            column="Feature:N",
            tooltip=[
                "main_genre",
                "Feature",
                "Value",
            ],
        )
        .properties(
            width=250
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


    