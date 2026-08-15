# app.py

import streamlit as st

from pages import (
    artist_explorer,
    temporal_trends,
    genre_comparison,
    prediction,
    music_rag_search,
)


# Page configuration
st.set_page_config(
    page_title="Music Analytics Dashboard",
    layout="wide",
)


# Main application
def main():

    # Sidebar
    st.sidebar.title("Dashboard Navigation")

    page = st.sidebar.radio(
        "Select a page:",
        [
            "Artist Explorer",
            "Temporal Trends",
            "Genre Comparison",
            "Predict Genre or Decade",
            "Music RAG Search",
        ],
    )

    # Page routing
    if page == "Artist Explorer":

        artist_explorer.show()

    elif page == "Temporal Trends":

        temporal_trends.show()

    elif page == "Genre Comparison":

        genre_comparison.show()

    elif page == "Predict Genre or Decade":

        prediction.show()

    elif page == "Music RAG Search":

        music_rag_search.show()


# Run application
if __name__ == "__main__":
    main()
