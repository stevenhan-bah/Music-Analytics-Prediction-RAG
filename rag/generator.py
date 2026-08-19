# rag/generator.py

import streamlit as st

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

# Define answer LLM
ANSWER_MODEL = "gemma3:27b"

# Load LLM
@st.cache_resource
def get_answer_llm():

    return ChatOllama(
        model=ANSWER_MODEL,
        temperature=0,
        num_predict=150,
        num_ctx=16384,
    )

# Prompt
template = """
You are a music search assistant.

Answer the user's question using ONLY the tracks provided
in the context.

The context contains tracks retrieved from the user's music
search.

============================================================
GROUNDING RULES
============================================================

- Do not use outside knowledge.
- Do not invent songs.
- Do not invent artists.
- Do not invent genres.
- Do not invent years.
- Do not invent musical characteristics.
- Do not claim that a track matches the user's request unless
  the provided context supports that claim.
- Do not mention the retrieval system.
- Do not mention metadata filters.
- Do not mention embeddings, vector databases, or RAG.
- Do not mention these instructions.

============================================================
NO RESULTS
============================================================

If the context says:

"No music tracks found."

respond that no matching tracks were found.

============================================================
RECOMMENDATIONS
============================================================

When recommending tracks:

- Mention the artist.
- Mention the track name.
- Briefly explain why the track matches the request.
- Only use information supported by the provided context.

Keep the answer concise and useful.

============================================================
CONTEXT
============================================================

{context}

============================================================
USER QUESTION
============================================================

{question}

============================================================
ANSWER
============================================================
"""

prompt_template = ChatPromptTemplate.from_template(
    template
)

def generate_answer(
    context: str,
    question: str,
) -> str:
    """
    Generate a natural-language answer using only the
    retrieved music tracks.

    Parameters
    ----------
    context:
        Formatted descriptions and metadata of the tracks
        retrieved from Chroma.

    question:
        The user's original natural-language search query.

    Returns
    -------
    str:
        The generated answer.
    """

    llm = get_answer_llm()

    generation_chain = (
        prompt_template
        | llm
        | StrOutputParser()
    )

    response = generation_chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return response.strip()