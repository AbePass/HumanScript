from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
import openai
import config 


CHROMA_PATH = "rag_files"

PROMPT_TEMPLATE = """
Here are skills that are relevant to the question:

{context}

---

use these if they will help answer the question: {question}
"""

RELEVANCE_THRESHOLD = 0.7  # Set your relevance threshold here

def query_vector_database(query_text):
    openai_key = config.openai_key

    # Prepare the DB.
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_key)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=1)
    if len(results) == 0:
        return (None, None)

    # Filter results based on relevance threshold
    filtered_results = [(doc, score) for doc, score in results if score >= RELEVANCE_THRESHOLD]
    if not filtered_results:
        return (query_text, None)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in filtered_results])
    sources = [doc.metadata.get("source", None) for doc, _score in filtered_results]
    return (context_text, sources)