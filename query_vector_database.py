from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
import os
from config import CHROMA_PATH

def query_vector_database(query_text, selected_kbs):
    openai_key = os.environ["OPENAI_API_KEY"]
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_key)

    all_compressed_docs = []

    for kb in selected_kbs:
        db_path = os.path.join(CHROMA_PATH, kb)
        if not os.path.exists(db_path):
            print(f"Warning: Database for {kb} not found at {db_path}")
            continue

        # Prepare the DB and retriever for this knowledge base
        db = Chroma(persist_directory=db_path, embedding_function=embedding_function)
        base_retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 25})

        # Set up the contextual compression retriever
        llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview")
        compressor = LLMChainExtractor.from_llm(llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever
        )

        # Retrieve and compress relevant documents
        compressed_docs = compression_retriever.invoke(query_text)
        for doc in compressed_docs:
            doc.metadata['knowledge_base'] = kb  # Add KB info to metadata
        all_compressed_docs.extend(compressed_docs)

    # Sort all compressed docs by relevance (assuming there's a relevance score in metadata)
    all_compressed_docs.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)

    # Take the top 10 most relevant documents
    top_docs = all_compressed_docs[:10]

    # Format the context
    context = "\n\n".join(doc.page_content for doc in top_docs)

    # Get the sources with knowledge base information
    sources = [f"{doc.metadata.get('source', 'Unknown')} (KB: {doc.metadata['knowledge_base']})" for doc in top_docs]

    return context, sources