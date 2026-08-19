# pages/music_rag_search.py

import streamlit as st

from database import search_artists

from rag.retriever import (
    music_retriever,
    format_docs,
)

from rag.generator import (
    generate_answer,
)

# Configure min max years
MIN_RELEASE_YEAR = 1930
MAX_RELEASE_YEAR = 2026


def show():

    st.title("Music RAG Search")

    st.write(
        "Search the music collection using natural language. "
        "Describe the mood, energy, genre, instrumentation, "
        "style, or other musical characteristics. Use the "
        "filters below when you want to restrict the search "
        "by artist, decade, vocal/instrumental type, or "
        "release year."
    )

    st.divider()

    st.subheader("Music Search")

    if "music_query" not in st.session_state:

        st.session_state.music_query = ""

    st.text_input(
        "What are you looking for? (e.g. Find aggressive electronic songs, Find songs that feel happy and energetic, Give me relaxed and mellow tracks, Find vocal hip hop songs, Find energetic instrumental rock tracks, Find energetic but melodically tonal tracks)",
        placeholder=(
            "e.g. aggressive electronic songs"
        ),
        key="music_query",
    )

    st.subheader("Filters")

    st.caption(
        "All filters default to Any, which means no metadata "
        "filter will be applied."
    )

    # Artist
    st.write("**Artist**")

    artist_search = st.text_input(
        "Search for an artist",
        key="rag_artist_search",
        placeholder="Type an artist name...",
    )

    selected_artist = "Any"

    if artist_search.strip():

        matches = search_artists(
            artist_search.strip()
        )

        if matches:

            artist_options = [
                "Any"
            ] + matches

            selected_artist = st.selectbox(
                "Select artist",
                artist_options,
                key="rag_selected_artist",
            )

        else:

            st.warning(
                "No artists found."
            )

    else:

        selected_artist = "Any"

    # Decade
    decades = [
        "Any",
        "1930s",
        "1940s",
        "1950s",
        "1960s",
        "1970s",
        "1980s",
        "1990s",
        "2000s",
        "2010s",
        "2020s",
    ]

    selected_decade = st.selectbox(
        "Decade",
        decades,
        index=0,
        key="rag_decade",
    )

    # Vocal/Instrumental
    voice_options = [
        "Any",
        "vocal",
        "instrumental",
    ]

    selected_voice_instrumental = st.selectbox(
        "Type",
        voice_options,
        index=0,
        key="rag_voice_instrumental",
        format_func=lambda value: (
            "Any"
            if value == "Any"
            else value.capitalize()
        ),
    )

    # Release Year
    st.write("**Release Year**")

    year_col1, year_col2 = st.columns(2)

    with year_col1:

        release_year_min = st.selectbox(
            "Minimum year",
            ["Any"] + list(
                range(
                    MIN_RELEASE_YEAR,
                    MAX_RELEASE_YEAR + 1,
                )
            ),
            index=0,
            key="rag_release_year_min",
        )

    with year_col2:

        release_year_max = st.selectbox(
            "Maximum year",
            ["Any"] + list(
                range(
                    MIN_RELEASE_YEAR,
                    MAX_RELEASE_YEAR + 1,
                )
            ),
            index=0,
            key="rag_release_year_max",
        )

    # Check min year not greater than max year range
    if (
        release_year_min != "Any"
        and release_year_max != "Any"
        and release_year_min > release_year_max
    ):

        st.warning(
            "Minimum release year cannot be greater "
            "than maximum release year."
        )

    # Search options
    st.divider()

    k = st.slider(
        "Number of tracks to retrieve",
        min_value=1,
        max_value=20,
        value=10,
        help=(
            "Number of tracks retrieved from the Chroma "
            "vector database before generating the answer."
        ),
    )

    # Explain search
    with st.expander(
        "How search works"
    ):

        st.write(
            "**Semantic search**"
        )

        st.markdown(
            """
            > Find happy and energetic songs

            The text above is used as the **semantic search**.

            **Metadata filters**

            The filters above are controlled directly by you:

            - Artist
            - Decade
            - Vocal / instrumental
            - Minimum release year
            - Maximum release year

            Selecting **Any** means that filter is not applied.

            For example:

            > Search: `sad acoustic songs`

            > Artist: `Ed Sheeran`

            > Decade: `2010s`

            > Type: `Vocal`

            This performs semantic search for `sad acoustic songs`
            while restricting the results to the selected metadata.
            """
        )

    # Example queries
    # st.caption(
    #     "Example searches:"
    # )

    # example_queries = [
    #     "Find aggressive electronic songs",
    #     "Find songs that feel happy and energetic",
    #     "Give me relaxed and mellow tracks",
    #     "Find vocal hip hop songs",
    #     "Find energetic instrumental rock tracks",
    #     "Find energetic but melodically tonal tracks",
    # ]

    # cols = st.columns(3)

    # for i, example in enumerate(
    #     example_queries
    # ):

    #     with cols[i % 3]:

    #         if st.button(
    #             example,
    #             key=f"example_query_{i}",
    #             use_container_width=True,
    #         ):

    #             st.session_state.music_query = (
    #                 example
    #             )

    #             st.rerun()

    # Search button
    search_clicked = st.button(
        "Search",
        type="primary",
        use_container_width=True,
    )

    if not search_clicked:

        return


    query = (
        st.session_state.music_query.strip()
    )

    if not query:

        st.warning(
            "Please enter a description of the music "
            "you are looking for."
        )

        return


    if (
        release_year_min != "Any"
        and release_year_max != "Any"
        and release_year_min > release_year_max
    ):

        st.warning(
            "Please choose a minimum release year that "
            "is less than or equal to the maximum release year."
        )

        return
    
    # Convert any to none
    artist_filter = (
        None
        if selected_artist == "Any"
        else selected_artist
    )

    decade_filter = (
        None
        if selected_decade == "Any"
        else selected_decade
    )

    voice_filter = (
        None
        if selected_voice_instrumental == "Any"
        else selected_voice_instrumental
    )

    year_min_filter = (
        None
        if release_year_min == "Any"
        else release_year_min
    )

    year_max_filter = (
        None
        if release_year_max == "Any"
        else release_year_max
    )

    # Display active filters
    active_filters = []

    if artist_filter is not None:

        active_filters.append(
            f"Artist: {artist_filter}"
        )

    if decade_filter is not None:

        active_filters.append(
            f"Decade: {decade_filter}"
        )

    if voice_filter is not None:

        active_filters.append(
            f"Type: {voice_filter.capitalize()}"
        )

    if year_min_filter is not None:

        active_filters.append(
            f"Year ≥ {year_min_filter}"
        )

    if year_max_filter is not None:

        active_filters.append(
            f"Year ≤ {year_max_filter}"
        )

    if active_filters:

        st.info(
            "**Active filters:** "
            + " • ".join(active_filters)
        )

    else:

        st.info(
            "No metadata filters selected. "
            "Searching the entire music collection."
        )

    # Run RAG
    with st.spinner(
        f'Searching the music collection for "{query}"...'
    ):

        try:

            (
                docs,
                search,
                chroma_filter,
            ) = music_retriever(
                user_query=query,
                artist=artist_filter,
                decade=decade_filter,
                voice_instrumental=voice_filter,
                release_year_min=year_min_filter,
                release_year_max=year_max_filter,
                k=k,
            )

            context = format_docs(
                docs
            )

            answer = generate_answer(
                context=context,
                question=query,
            )

        except ValueError as e:

            st.warning(
                str(e)
            )

            return

        except Exception as e:

            st.error(
                "An error occurred while searching "
                "the music database."
            )

            st.exception(e)

            return

    st.subheader(
        "Answer"
    )

    st.write(
        answer
    )

    st.divider()


    st.subheader(
        f"Retrieved Tracks ({len(docs)})"
    )

    if not docs:

        st.info(
            "No tracks were found for this search."
        )

    else:

        for i, doc in enumerate(
            docs,
            start=1,
        ):

            metadata = doc.metadata

            artist = metadata.get(
                "artist",
                "Unknown Artist",
            )

            track = metadata.get(
                "release_name",
                "Unknown Track",
            )

            genre = metadata.get(
                "main_genre",
                "Unknown Genre",
            )

            year = metadata.get(
                "release_year",
                "Unknown Year",
            )

            with st.expander(
                f"{i}. {track} — {artist}"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Artist:** {artist}"
                    )

                    st.write(
                        f"**Track:** {track}"
                    )

                    st.write(
                        f"**Genre:** {genre}"
                    )

                with col2:

                    st.write(
                        f"**Year:** {year}"
                    )

                    if "decade" in metadata:

                        st.write(
                            f"**Decade:** "
                            f"{metadata['decade']}"
                        )

                    if (
                        "voice_instrumental"
                        in metadata
                    ):

                        st.write(
                            f"**Type:** "
                            f"{metadata['voice_instrumental']}"
                        )

                st.write(
                    "**Description:**"
                )

                st.write(
                    doc.page_content
                )

    # Search details
    with st.expander(
        "Search Details"
    ):

        st.write(
            "**Semantic query:**"
        )

        st.code(
            search.semantic_query
        )

        st.write(
            "**Artist filter:**"
        )

        st.code(
            artist_filter
            if artist_filter is not None
            else "Any"
        )

        st.write(
            "**Decade filter:**"
        )

        st.code(
            decade_filter
            if decade_filter is not None
            else "Any"
        )

        st.write(
            "**Vocal / instrumental filter:**"
        )

        st.code(
            voice_filter
            if voice_filter is not None
            else "Any"
        )

        st.write(
            "**Minimum release year:**"
        )

        st.code(
            str(year_min_filter)
            if year_min_filter is not None
            else "Any"
        )

        st.write(
            "**Maximum release year:**"
        )

        st.code(
            str(year_max_filter)
            if year_max_filter is not None
            else "Any"
        )

        st.write(
            "**Chroma metadata filter:**"
        )

        if chroma_filter:

            st.json(
                chroma_filter
            )

        else:

            st.write(
                "No metadata filters."
            )

        st.write(
            f"**Number of retrieved documents:** "
            f"{len(docs)}"
        )