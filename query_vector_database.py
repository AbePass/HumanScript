from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
import os

CHROMA_PATH = "db"

def query_vector_database(query_text):
    openai_key = os.environ["OPENAI_API_KEY"]

    # Prepare the DB and retriever
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_key)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    base_retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 10, "fetch_k": 50})

    # Set up the contextual compression retriever
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
    compressor = LLMChainExtractor.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )

    # Retrieve and compress relevant documents
    compressed_docs = compression_retriever.invoke(query_text)

    # Format the context
    context = "\n\n".join(doc.page_content for doc in compressed_docs)

    # Get the sources
    sources = [doc.metadata.get("source", None) for doc in compressed_docs]

    return context, sources