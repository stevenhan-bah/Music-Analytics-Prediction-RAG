# Temporal Trends page

import streamlit as st
import altair as alt

from config import FEATURE_OPTIONS

from database import (
    get_loudness_by_decade,
    get_two_feature_trend,
)


def show():

    st.title("Temporal Trends")


    # Average Loudness by Decade
    st.subheader(
        "Average Loudness by Decade"
    )

    loudness_data = get_loudness_by_decade()


    loudness_chart = (
        alt.Chart(loudness_data)
        .mark_bar(
            color="steelblue"
        )
        .encode(
            x=alt.X(
                "decade:O",
                title="Decade"
            ),
            y=alt.Y(
                "average_loudness:Q",
                title="Average Loudness"
            ),
            tooltip=[
                "decade",
                "average_loudness"
            ]
        )
        .properties(
            title="Average Loudness by Decade",
            width=800,
            height=400,
        )
    )


    st.altair_chart(
        loudness_chart,
        use_container_width=True
    )


    # Compare Two Features
    st.subheader(
        "Two Feature Comparison Over Time"
    )


    selected_features = st.multiselect(
        "Select exactly two features:",
        FEATURE_OPTIONS,
        default=[
            "danceability",
            "bpm"
        ],
        max_selections=2
    )


    if len(selected_features) != 2:

        st.warning(
            "Please select exactly two features."
        )

        return


    feature_data = get_two_feature_trend(
        selected_features[0],
        selected_features[1]
    )


    feature1 = selected_features[0]
    feature2 = selected_features[1]


    # Line for first feature
    line1 = (
        alt.Chart(feature_data)
        .mark_line(
            color="blue",
            point=True
        )
        .encode(
            x=alt.X(
                "decade:O",
                title="Decade"
            ),
            y=alt.Y(
                f"{feature1}:Q",
                title=feature1,
                axis=alt.Axis(
                    titleColor="blue"
                )
            ),
            tooltip=[
                "decade",
                feature1
            ]
        )
    )


    # Line for second feature
    line2 = (
        alt.Chart(feature_data)
        .mark_line(
            color="red",
            point=True
        )
        .encode(
            x=alt.X(
                "decade:O",
                title="Decade"
            ),
            y=alt.Y(
                f"{feature2}:Q",
                title=feature2,
                axis=alt.Axis(
                    titleColor="red"
                )
            ),
            tooltip=[
                "decade",
                feature2
            ]
        )
    )


    combined_chart = (
        alt.layer(
            line1,
            line2
        )
        .resolve_scale(
            y="independent"
        )
        .properties(
            title="Feature Trends by Decade",
            width=800,
            height=400,
        )
    )


    st.altair_chart(
        combined_chart,
        use_container_width=True
    )