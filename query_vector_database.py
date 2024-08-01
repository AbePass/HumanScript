from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

CHROMA_PATH = "db"

RELEVANCE_THRESHOLD = 0.7  # Set your relevance threshold here

def query_vector_database(query_text):
    openai_key = os.environ["OPENAI_API_KEY"]

    # Prepare the DB.
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_key)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Get the total number of elements in the database
    total_elements = db._collection.count()
    
    # Adjust k to be the minimum of 10 and the total number of elements
    k = min(10, total_elements)
    
    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=k)
    if len(results) == 0:
        return (None, None)

    # Filter results based on relevance threshold
    filtered_results = [(doc, score) for doc, score in results if score >= RELEVANCE_THRESHOLD]
    if not filtered_results:
        return (query_text, None)

    # Construct context text only from filtered results
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in filtered_results])
    sources = [doc.metadata.get("source", None) for doc, _score in filtered_results]
    return (context_text, sources)