# Load the models and scalers from the pickle files

import pickle
import joblib
import streamlit as st


@st.cache_resource
def load_genre_model():
    with open(
        "notebook/models/catboost_genre_model_features_selected.pkl",
        "rb"
    ) as file:
        return pickle.load(file)


@st.cache_resource
def load_decade_model():
    with open(
        "notebook/models/catboost_decade_model_features_selected.pkl",
        "rb"
    ) as file:
        return pickle.load(file)


@st.cache_resource
def load_genre_minmax_scaler():
    return joblib.load(
        "notebook/models/genre_minmax_scaler.pkl"
    )


@st.cache_resource
def load_genre_standard_scaler():
    return joblib.load(
        "notebook/models/genre_standard_scaler.pkl"
    )

@st.cache_resource
def load_decade_minmax_scaler():
    return joblib.load(
        "notebook/models/decades_minmax_scaler.pkl"
    )


@st.cache_resource
def load_decade_standard_scaler():
    return joblib.load(
        "notebook/models/decades_standard_scaler.pkl"
    )