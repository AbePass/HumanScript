from langchain_community.document_loaders import DirectoryLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
import shutil

# Load environment variables
load_dotenv()

CHROMA_PATH = "db"
KNOWLEDGE_BASE_PATH = "knowledge_bases"

def load_docs_folder(knowledge_base):
    kb_path = os.path.join(KNOWLEDGE_BASE_PATH, knowledge_base)
    docs_path = os.path.join(kb_path, "docs")
    urls_file = os.path.join(kb_path, "urls.txt")

    # Load and process documents
    documents = load_documents(docs_path, urls_file)
    chunks = split_text(documents)
    save_to_chroma(chunks, knowledge_base)

def load_documents(docs_path, urls_file):
    # Load local documents
    local_loader = DirectoryLoader(docs_path, glob="*.*")
    local_documents = local_loader.load()
    print(f"Loaded {len(local_documents)} local documents from {docs_path}")

    # Load URLs
    url_documents = load_urls(urls_file)
    
    # Combine local and URL documents
    all_documents = local_documents + url_documents
    print(f"Total documents loaded: {len(all_documents)}")
    return all_documents

def load_urls(urls_file):
    if not os.path.exists(urls_file):
        print(f"No {urls_file} found. Skipping URL loading.")
        return []

    with open(urls_file, 'r') as file:
        urls = file.read().splitlines()

    url_documents = []
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            url_documents.extend(loader.load())
            print(f"Loaded content from: {url}")
        except Exception as e:
            print(f"Error loading {url}: {e}")

    print(f"Loaded {len(url_documents)} documents from URLs")
    return url_documents

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks: list[Document], knowledge_base: str):
    db_path = os.path.join(CHROMA_PATH, knowledge_base)
    # Remove existing DB files
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    # Create a new DB from the documents
    embedding_function = OpenAIEmbeddings()
    db = Chroma.from_documents(
        chunks, embedding_function, persist_directory=db_path
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {db_path}.")

if __name__ == "__main__":
    # Get all subdirectories in the KNOWLEDGE_BASE_PATH
    knowledge_bases = [d for d in os.listdir(KNOWLEDGE_BASE_PATH) 
                       if os.path.isdir(os.path.join(KNOWLEDGE_BASE_PATH, d))]
    
    for kb in knowledge_bases:
        print(f"Processing knowledge base: {kb}")
        load_docs_folder(kb)