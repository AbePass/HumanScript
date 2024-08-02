from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

CHROMA_PATH = "db"

def query_vector_database(query_text):
    openai_key = os.environ["OPENAI_API_KEY"]

    # Prepare the DB and retriever
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_key)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 6})

    # Retrieve relevant documents
    docs = retriever.invoke(query_text)

    # Format the context
    context = "\n\n".join(doc.page_content for doc in docs)

    # Get the sources
    sources = [doc.metadata.get("source", None) for doc in docs]

    return context, sources