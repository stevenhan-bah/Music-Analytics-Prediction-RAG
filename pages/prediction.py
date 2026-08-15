# Prediction page

import streamlit as st
import pandas as pd
import numpy as np

from config import (
    FEATURE_LIMITS,
    TRAINING_COLUMNS_ORDER,
    GENRE_LABELS,
    DECADE_LABELS,
)

from models import (
    load_genre_model,
    load_decade_model,
    load_genre_minmax_scaler,
    load_genre_standard_scaler,
    load_decade_minmax_scaler,
    load_decade_standard_scaler,
)

# Get user input for the features
def get_user_input():

    return pd.DataFrame([{

        "mfcc_zero_mean": st.number_input(
            "MFCC Zero Mean (-1100.0, -450.0)",
            -1100.0,
            -450.0,
            -700.0
        ),

        "onset_rate": st.number_input(
            "Onset Rate (0.0, 24.0)",
            0.0,
            24.0,
            8.0
        ),

        "average_loudness": st.number_input(
            "Average Loudness (0.0, 1.0)",
            0.0,
            1.0,
            0.5
        ),

        "danceability": st.number_input(
            "Danceability (0.0, 3.0)",
            0.0,
            3.0,
            1.5
        ),

        "voice_instrumental": st.selectbox(
            "Voice Instrumental (0, 1)",
            [0, 1]
        ),

        "mood_acoustic": st.selectbox(
            "Mood Acoustic (0, 1)",
            [0, 1]
        ),

        "mood_electronic": st.selectbox(
            "Mood Electronic (0, 1)",
            [0, 1]
        ),

        "tuning_equal_tempered_deviation": st.number_input(
            "Tuning Equal Tempered Deviation (0.0, 0.5)",
            0.0,
            0.5,
            0.1
        ),

        "bpm": st.number_input(
            "BPM (40, 200)",
            40,
            200,
            120
        ),

        "tuning_frequency": st.number_input(
            "Tuning Frequency (430.0, 460.0)",
            430.0,
            460.0,
            440.0
        ),

        "timbre": st.selectbox(
            "Timbre (0, 1)",
            [0, 1]
        ),

        "dynamic_complexity": st.number_input(
            "Dynamic Complexity (0.0, 80.0)",
            0.0,
            80.0,
            40.0
        ),

        "mood_aggressive_prob": st.number_input(
            "Mood Aggressive Probability (0.0, 1.0)",
            0.0,
            1.0,
            0.5
        ),

        "mood_happy_prob": st.number_input(
            "Mood Happy Probability (0.0, 1.0)",
            0.0,
            1.0,
            0.5
        )

    }])


# Feature processing functions

# Clamp the features to the limits
def clamp_features(df):

    df = df.copy()

    for feature, (low, high) in FEATURE_LIMITS.items():

        if feature in df.columns:
            df[feature] = df[feature].clip(
                lower=low,
                upper=high
            )

    return df

# Preprocess the features with clamping, minmax scaling, log transformation, and standard scaling
def preprocess_features(
    df,
    minmax_scaler,
    standard_scaler
):

    df = clamp_features(df)


    # MinMax scaling
    minmax_cols = [
        "mood_happy_prob",
        "mood_aggressive_prob",
    ]

    df[minmax_cols] = minmax_scaler.transform(
        df[minmax_cols]
    )


    # Log transformation
    log_cols = [
        "onset_rate",
        "dynamic_complexity",
        "tuning_equal_tempered_deviation",
    ]

    df[log_cols] = np.log1p(
        df[log_cols]
    )


    # Standard scaling
    standard_cols = [
        "bpm",
        "danceability",
        "mfcc_zero_mean",
        "tuning_frequency",
        "onset_rate",
        "dynamic_complexity",
        "tuning_equal_tempered_deviation",
    ]

    df[standard_cols] = standard_scaler.transform(
        df[standard_cols]
    )


    return df[
        TRAINING_COLUMNS_ORDER
    ]


# Streamlit page function
def show():

    st.title(
        "Predict Genre or Decade"
    )

    st.subheader(
        "Enter Audio Features"
    )


    features = get_user_input()


    genre_model = load_genre_model()
    decade_model = load_decade_model()


    col1, col2 = st.columns(2)


    # Genre prediction
    with col1:

        if st.button(
            "Predict Genre"
        ):

            genre_features = preprocess_features(
                features,
                load_genre_minmax_scaler(),
                load_genre_standard_scaler()
            )

            # Get probabilities for all genres
            probabilities = genre_model.predict_proba(
                genre_features
            )[0]

            # Get the predicted genre
            prediction = int(
                np.argmax(probabilities)
            )

            st.success(
                f"The predicted genre is: {GENRE_LABELS[prediction]}"
            )

            # Create probability DataFrame
            probability_df = pd.DataFrame({
                "Genre": [
                    GENRE_LABELS[i]
                    for i in range(len(probabilities))
                ],
                "Probability": probabilities
            })

            # Convert probabilities to percentages
            probability_df["Probability"] = (
                probability_df["Probability"] * 100
            )

            # Sort from highest to lowest
            probability_df = probability_df.sort_values(
                "Probability",
                ascending=False
            )

            st.subheader(
                "Genre Probabilities"
            )

            # Display probability bars
            st.dataframe(
                probability_df,
                hide_index=True,
                column_config={
                    "Probability": st.column_config.ProgressColumn(
                        "Probability",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100
                    )
                }
            )

    # Decade prediction
    with col2:

        if st.button(
            "Predict Decade"
        ):

            decade_features = preprocess_features(
                features,
                load_decade_minmax_scaler(),
                load_decade_standard_scaler()
            )

            # Get probabilities for all genres
            probabilities = decade_model.predict_proba(
                decade_features
            )[0]

            # Get the predicted genre
            prediction = int(
                np.argmax(probabilities)
            )

            st.success(
                f"The predicted decade is: {DECADE_LABELS[prediction]}"
            )

            # Create probability DataFrame
            probability_df = pd.DataFrame({
                "Decade": [
                    DECADE_LABELS[i]
                    for i in range(len(probabilities))
                ],
                "Probability": probabilities
            })

            # Convert probabilities to percentages
            probability_df["Probability"] = (
                probability_df["Probability"] * 100
            )

            # Sort from highest to lowest
            probability_df = probability_df.sort_values(
                "Probability",
                ascending=False
            )

            st.subheader(
                "Decade Probabilities"
            )

            # Display probability bars
            st.dataframe(
                probability_df,
                hide_index=True,
                column_config={
                    "Probability": st.column_config.ProgressColumn(
                        "Probability",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100
                    )
                }
            )