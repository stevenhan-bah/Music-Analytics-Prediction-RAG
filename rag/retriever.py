# rag/retriever.py

import streamlit as st

from typing import Optional

from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Configuration
CHROMA_DIR = "./notebook/music_chroma_db"

EMBEDDING_MODEL = "nomic-embed-text"


# Load chroma vector store
@st.cache_resource
def get_vector_store():

    embedding_function = OllamaEmbeddings(
        model=EMBEDDING_MODEL
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embedding_function,
    )

    return vector_store


# Search request schema
class SearchRequest(BaseModel):

    semantic_query: str

    # None means "Any" or no filter.
    artist: Optional[str] = None

    decade: Optional[str] = None

    voice_instrumental: Optional[str] = None

    release_year_min: Optional[int] = None

    release_year_max: Optional[int] = None


# Define clean_value function
def clean_value(value):

    """
    Normalize values coming from the Streamlit controls.

    Streamlit controls can use "Any" to represent no filter.
    This converts that value to None so it is not included
    in the Chroma metadata filter.
    """

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip()

        if value.lower() in {
            "",
            "any",
            "empty",
            "none",
            "null",
            "n/a",
        }:

            return None

    return value

# Build metadata filter
def build_filter(
    artist: Optional[str] = None,
    decade: Optional[str] = None,
    voice_instrumental: Optional[str] = None,
    release_year_min: Optional[int] = None,
    release_year_max: Optional[int] = None,
) -> dict:
    """
    Build a Chroma metadata filter from manually selected
    Streamlit filter values.

    Each individual condition contains exactly one Chroma
    comparison operator.
    """

    conditions = []

    # For artist
    artist = clean_value(artist)

    if artist:
        conditions.append(
            {
                "artist": {
                    "$eq": artist
                }
            }
        )

    # For decade
    decade = clean_value(decade)

    if decade:
        conditions.append(
            {
                "decade": {
                    "$eq": decade
                }
            }
        )

    # For voice/instrumental
    voice_instrumental = clean_value(
        voice_instrumental
    )

    if voice_instrumental:
        conditions.append(
            {
                "voice_instrumental": {
                    "$eq": voice_instrumental
                }
            }
        )

    # release year min
    if release_year_min is not None:
        conditions.append(
            {
                "release_year": {
                    "$gte": int(release_year_min)
                }
            }
        )

    # release year max
    if release_year_max is not None:
        conditions.append(
            {
                "release_year": {
                    "$lte": int(release_year_max)
                }
            }
        )

    # No filters
    if not conditions:
        return {}

    # 1 filter
    if len(conditions) == 1:
        return conditions[0]

    # multiple filters
    return {
        "$and": conditions
    }


# validate search request function
def validate_search_request(
    search: SearchRequest,
) -> tuple[bool, str]:

    """
    Validate the semantic portion of the search.

    Metadata-only searches are still not supported.

    For example:

        "sad energetic songs"
            -> valid

        artist = "Ed Sheeran"
        semantic query = "sad songs"
            -> valid

        artist = "Ed Sheeran"
        semantic query = ""
            -> invalid
    """

    semantic_query = clean_value(
        search.semantic_query
    )

    if not semantic_query:

        return (
            False,
            (
                "Your search needs to describe something "
                "about the music, such as its mood, energy, "
                "genre, style, instrumentation, or sound."
            ),
        )

    return True, ""

# retrieve music
def music_retriever(
    user_query: str,
    artist: Optional[str] = None,
    decade: Optional[str] = None,
    voice_instrumental: Optional[str] = None,
    release_year_min: Optional[int] = None,
    release_year_max: Optional[int] = None,
    k: int = 5,
):
    """
    Retrieve music using:

    1. The user's natural-language query as the semantic query.
    2. Optional metadata filters supplied by the Streamlit UI.

    Metadata is NOT inferred from the user's natural-language
    query.

    Parameters
    ----------
    user_query:
        Semantic music search entered by the user.

    artist:
        Artist selected in the Streamlit UI.
        None / "Any" means no artist filter.

    decade:
        Decade selected in the Streamlit UI.
        None / "Any" means no decade filter.

    voice_instrumental:
        "vocal", "instrumental", or None.

    release_year_min:
        Minimum release year, or None.

    release_year_max:
        Maximum release year, or None.

    k:
        Number of documents to retrieve.

    Returns
    -------
    docs:
        Retrieved Chroma documents.

    search:
        SearchRequest containing the actual semantic query
        and UI-selected metadata values.

    chroma_filter:
        The metadata filter passed to Chroma.
    """

    search = SearchRequest(
        semantic_query=user_query.strip(),
        artist=clean_value(artist),
        decade=clean_value(decade),
        voice_instrumental=clean_value(
            voice_instrumental
        ),
        release_year_min=release_year_min,
        release_year_max=release_year_max,
    )

    valid, error_message = (
        validate_search_request(search)
    )

    if not valid:

        raise ValueError(
            error_message
        )


    chroma_filter = build_filter(
        artist=artist,
        decade=decade,
        voice_instrumental=voice_instrumental,
        release_year_min=release_year_min,
        release_year_max=release_year_max,
    )

    semantic_query = clean_value(
        search.semantic_query
    )

    semantic_query = semantic_query.strip()

    vector_store = get_vector_store()

    docs = vector_store.similarity_search(
        query=semantic_query,
        filter=(
            chroma_filter
            if chroma_filter
            else None
        ),
        k=k,
    )

    return (
        docs,
        search,
        chroma_filter,
    )


# Format retrieved docs
def format_docs(docs) -> str:
    """
    Convert retrieved Chroma documents into text context
    for the answer-generation LLM.
    """

    if not docs:

        return "No music tracks found."

    formatted = []

    for doc in docs:

        artist = doc.metadata.get(
            "artist",
            "Unknown",
        )

        track = doc.metadata.get(
            "release_name",
            "Unknown",
        )

        genre = doc.metadata.get(
            "main_genre",
            "Unknown",
        )

        year = doc.metadata.get(
            "release_year",
            "Unknown",
        )

        description = doc.page_content

        formatted.append(
            f"""
Artist: {artist}
Track: {track}
Genre: {genre}
Year: {year}

Description:
{description}
"""
        )

    return "\n\n".join(
        formatted
    )